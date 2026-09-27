import asyncio
import os
import sqlite3
from datetime import datetime, timedelta

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN1")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

db = sqlite3.connect("schedule.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    day TEXT NOT NULL,
    subject TEXT NOT NULL,
    time TEXT NOT NULL,
    classroom TEXT NOT NULL,
    reminder_minutes INTEGER NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    reminders_enabled INTEGER DEFAULT 1
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    schedule_id INTEGER NOT NULL,
    notification_date TEXT NOT NULL,
    UNIQUE(user_id, schedule_id, notification_date)
)
""")

db.commit()

days = [
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье"
]

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить занятие"),
         KeyboardButton(text="📚 Моё расписание")],
        [KeyboardButton(text="📅 Выбрать день"),
         KeyboardButton(text="✏️ Изменить занятие")],
        [KeyboardButton(text="🗑 Удалить занятие"),
         KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="🔔 Напоминания")]
    ],
    resize_keyboard=True
)


class AddLesson(StatesGroup):
    waiting_for_day = State()
    subject = State()
    time = State()
    classroom = State()
    reminder = State()


class EditLesson(StatesGroup):
    subject = State()
    day = State()
    time = State()
    classroom = State()
    reminder = State()


def day_keyboard():
    buttons = []

    for day in days:
        buttons.append([
            InlineKeyboardButton(
                text=day,
                callback_data=f"day_{day}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def delete_keyboard(user_id):
    cursor.execute(
        "SELECT id, subject, day, time FROM schedule WHERE user_id = ? ORDER BY id",
        (user_id,)
    )

    lessons = cursor.fetchall()

    buttons = []

    for lesson_id, subject, day, time in lessons:
        buttons.append([
            InlineKeyboardButton(
                text=f"🗑 {subject} — {day} {time}",
                callback_data=f"delete_{lesson_id}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def edit_keyboard(user_id):
    cursor.execute(
        "SELECT id, subject, day, time FROM schedule WHERE user_id = ? ORDER BY id",
        (user_id,)
    )

    lessons = cursor.fetchall()

    buttons = []

    for lesson_id, subject, day, time in lessons:
        buttons.append([
            InlineKeyboardButton(
                text=f"✏️ {subject} — {day} {time}",
                callback_data=f"edit_{lesson_id}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def reminder_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔔 Включить",
                    callback_data="reminders_on"
                ),
                InlineKeyboardButton(
                    text="🔕 Выключить",
                    callback_data="reminders_off"
                )
            ]
        ]
    )


@router.message(Command("start"))
async def start_command(message: Message):
    user_id = message.from_user.id

    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, reminders_enabled) VALUES (?, 1)",
        (user_id,)
    )

    db.commit()

    await message.answer(
        "🧠 Добро пожаловать!\n\n"
        "Выберите действие:",
        reply_markup=main_keyboard
    )


@router.message(lambda message: message.text == "➕ Добавить занятие")
async def add_lesson(message: Message, state: FSMContext):
    await state.set_state(AddLesson.waiting_for_day)

    await message.answer(
        "📅 Выберите день:",
        reply_markup=day_keyboard()
    )


@router.callback_query(
    lambda callback: callback.data.startswith("day_")
)
async def choose_day(callback: CallbackQuery, state: FSMContext):
    day = callback.data.replace("day_", "")

    current_state = await state.get_state()

    if current_state == AddLesson.waiting_for_day.state:
        await state.update_data(day=day)
        await state.set_state(AddLesson.subject)

        await callback.message.answer(
            f"📅 День: {day}\n\n"
            "📚 Введите название предмета:"
        )

    await callback.answer()


@router.message(AddLesson.subject)
async def enter_subject(message: Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await state.set_state(AddLesson.time)

    await message.answer(
        "⏰ Введите время занятия в формате ЧЧ:ММ\n"
        "Например: 09:30"
    )


@router.message(AddLesson.time)
async def enter_time(message: Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%H:%M")
    except ValueError:
        await message.answer(
            "❌ Неверный формат.\n"
            "Введите время например: 09:30"
        )
        return

    await state.update_data(time=message.text)
    await state.set_state(AddLesson.classroom)

    await message.answer("🚪 Введите номер кабинета:")


@router.message(AddLesson.classroom)
async def enter_classroom(message: Message, state: FSMContext):
    await state.update_data(classroom=message.text)
    await state.set_state(AddLesson.reminder)

    await message.answer(
        "🔔 За сколько минут напоминать?\n"
        "Можно от 1 до 1440 минут."
    )


@router.message(AddLesson.reminder)
async def enter_reminder(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer(
            "❌ Введите только число.\n"
            "Например: 30"
        )
        return

    reminder = int(message.text)

    if reminder < 1 or reminder > 1440:
        await message.answer(
            "❌ Можно указать от 1 до 1440 минут."
        )
        return

    data = await state.get_data()

    cursor.execute(
        """
        INSERT INTO schedule
        (user_id, day, subject, time, classroom, reminder_minutes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            message.from_user.id,
            data["day"],
            data["subject"],
            data["time"],
            data["classroom"],
            reminder
        )
    )

    db.commit()

    await state.clear()

    await message.answer(
        "✅ Занятие добавлено!\n\n"
        f"📅 {data['day']}\n"
        f"📚 {data['subject']}\n"
        f"⏰ {data['time']}\n"
        f"🚪 Кабинет: {data['classroom']}\n"
        f"🔔 Напоминание: за {reminder} мин.",
        reply_markup=main_keyboard
    )


@router.message(lambda message: message.text == "📚 Моё расписание")
async def my_schedule(message: Message):
    cursor.execute(
        """
        SELECT day, subject, time, classroom
        FROM schedule
        WHERE user_id = ?
        ORDER BY id
        """,
        (message.from_user.id,)
    )

    lessons = cursor.fetchall()

    if not lessons:
        await message.answer("📭 У вас пока нет занятий.")
        return

    text = "📚 Моё расписание:\n\n"

    for day, subject, time, classroom in lessons:
        text += (
            f"📅 {day}\n"
            f"📚 {subject}\n"
            f"⏰ {time}\n"
            f"🚪 Кабинет: {classroom}\n\n"
        )

    await message.answer(text)


@router.message(lambda message: message.text == "📅 Выбрать день")
async def choose_day_menu(message: Message):
    await message.answer(
        "📅 Выберите день:",
        reply_markup=day_keyboard()
    )


@router.callback_query(
    lambda callback: callback.data.startswith("day_")
)
async def show_day(callback: CallbackQuery):
    day = callback.data.replace("day_", "")

    cursor.execute(
        """
        SELECT subject, time, classroom
        FROM schedule
        WHERE user_id = ? AND day = ?
        ORDER BY time
        """,
        (callback.from_user.id, day)
    )

    lessons = cursor.fetchall()

    if not lessons:
        await callback.message.answer(
            f"📭 В {day.lower()} занятий нет."
        )
    else:
        text = f"📅 {day}:\n\n"

        for subject, time, classroom in lessons:
            text += (
                f"📚 {subject}\n"
                f"⏰ {time}\n"
                f"🚪 Кабинет: {classroom}\n\n"
            )

        await callback.message.answer(text)

    await callback.answer()


@router.message(lambda message: message.text == "✏️ Изменить занятие")
async def edit_lesson(message: Message):
    cursor.execute(
        "SELECT id FROM schedule WHERE user_id = ?",
        (message.from_user.id,)
    )

    if cursor.fetchone() is None:
        await message.answer("📭 У вас пока нет занятий.")
        return

    await message.answer(
        "✏️ Выберите занятие, которое хотите изменить:",
        reply_markup=edit_keyboard(message.from_user.id)
    )


@router.callback_query(
    lambda callback: callback.data.startswith("edit_")
)
async def start_edit(callback: CallbackQuery, state: FSMContext):
    lesson_id = int(callback.data.replace("edit_", ""))

    cursor.execute(
        """
        SELECT subject, day, time, classroom, reminder_minutes
        FROM schedule
        WHERE id = ? AND user_id = ?
        """,
        (lesson_id, callback.from_user.id)
    )

    lesson = cursor.fetchone()

    if not lesson:
        await callback.answer("Занятие не найдено.")
        return

    await state.update_data(
        lesson_id=lesson_id,
        old_day=lesson[1],
        old_time=lesson[2],
        old_classroom=lesson[3],
        old_reminder=lesson[4]
    )

    await state.set_state(EditLesson.subject)

    await callback.message.answer(
        f"📚 Текущее название: {lesson[0]}\n\n"
        "Введите новое название:"
    )

    await callback.answer()


@router.message(EditLesson.subject)
async def edit_subject(message: Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await state.set_state(EditLesson.day)

    await message.answer(
        "📅 Выберите новый день:",
        reply_markup=day_keyboard()
    )


@router.callback_query(
    lambda callback: callback.data.startswith("day_")
)
async def edit_day(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()

    if current_state != EditLesson.day.state:
        await callback.answer()
        return

    day = callback.data.replace("day_", "")

    await state.update_data(day=day)
    await state.set_state(EditLesson.time)

    await callback.message.answer(
        "⏰ Введите новое время в формате ЧЧ:ММ\n"
        "Например: 10:30"
    )

    await callback.answer()


@router.message(EditLesson.time)
async def edit_time(message: Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%H:%M")
    except ValueError:
        await message.answer(
            "❌ Неверный формат.\n"
            "Введите например: 10:30"
        )
        return

    await state.update_data(time=message.text)
    await state.set_state(EditLesson.classroom)

    await message.answer("🚪 Введите новый кабинет:")


@router.message(EditLesson.classroom)
async def edit_classroom(message: Message, state: FSMContext):
    await state.update_data(classroom=message.text)
    await state.set_state(EditLesson.reminder)

    await message.answer(
        "🔔 Введите новое напоминание от 1 до 1440 минут:"
    )


@router.message(EditLesson.reminder)
async def edit_reminder(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer(
            "❌ Введите только число."
        )
        return

    reminder = int(message.text)

    if reminder < 1 or reminder > 1440:
        await message.answer(
            "❌ Можно указать от 1 до 1440 минут."
        )
        return

    data = await state.get_data()

    cursor.execute(
        """
        UPDATE schedule
        SET subject = ?,
            day = ?,
            time = ?,
            classroom = ?,
            reminder_minutes = ?
        WHERE id = ? AND user_id = ?
        """,
        (
            data["subject"],
            data["day"],
            data["time"],
            data["classroom"],
            reminder,
            data["lesson_id"],
            message.from_user.id
        )
    )

    db.commit()

    await state.clear()

    await message.answer(
        "✅ Занятие успешно изменено!\n\n"
        f"📅 {data['day']}\n"
        f"📚 {data['subject']}\n"
        f"⏰ {data['time']}\n"
        f"🚪 Кабинет: {data['classroom']}\n"
        f"🔔 Напоминание: за {reminder} мин.",
        reply_markup=main_keyboard
    )


@router.message(lambda message: message.text == "🗑 Удалить занятие")
async def delete_lesson(message: Message):
    cursor.execute(
        "SELECT id FROM schedule WHERE user_id = ?",
        (message.from_user.id,)
    )

    if cursor.fetchone() is None:
        await message.answer("📭 У вас нет занятий для удаления.")
        return

    await message.answer(
        "🗑 Выберите занятие для удаления:",
        reply_markup=delete_keyboard(message.from_user.id)
    )


@router.callback_query(
    lambda callback: callback.data.startswith("delete_")
)
async def delete_callback(callback: CallbackQuery):
    lesson_id = int(callback.data.replace("delete_", ""))

    cursor.execute(
        "DELETE FROM schedule WHERE id = ? AND user_id = ?",
        (lesson_id, callback.from_user.id)
    )

    db.commit()

    await callback.message.edit_text("✅ Занятие удалено.")
    await callback.answer()


@router.message(lambda message: message.text == "📊 Статистика")
async def statistics(message: Message):
    user_id = message.from_user.id

    cursor.execute(
        "SELECT COUNT(*) FROM schedule WHERE user_id = ?",
        (user_id,)
    )

    total = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(DISTINCT subject) FROM schedule WHERE user_id = ?",
        (user_id,)
    )

    subjects = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT day, COUNT(*)
        FROM schedule
        WHERE user_id = ?
        GROUP BY day
        """,
        (user_id,)
    )

    by_day = cursor.fetchall()

    text = (
        "📊 Статистика\n\n"
        f"📚 Всего занятий: {total}\n"
        f"📖 Разных предметов: {subjects}\n\n"
    )

    if by_day:
        text += "По дням:\n"

        for day, count in by_day:
            text += f"📅 {day}: {count}\n"

    await message.answer(text)


@router.message(lambda message: message.text == "🔔 Напоминания")
async def reminders(message: Message):
    cursor.execute(
        "SELECT reminders_enabled FROM users WHERE user_id = ?",
        (message.from_user.id,)
    )

    result = cursor.fetchone()

    enabled = result[0] if result else 1

    status = "включены 🔔" if enabled else "выключены 🔕"

    await message.answer(
        f"🔔 Напоминания сейчас {status}.",
        reply_markup=reminder_keyboard()
    )


@router.callback_query(
    lambda callback: callback.data == "reminders_on"
)
async def reminders_on(callback: CallbackQuery):
    cursor.execute(
        """
        INSERT INTO users (user_id, reminders_enabled)
        VALUES (?, 1)
        ON CONFLICT(user_id)
        DO UPDATE SET reminders_enabled = 1
        """,
        (callback.from_user.id,)
    )

    db.commit()

    await callback.message.edit_text("🔔 Напоминания включены.")
    await callback.answer()


@router.callback_query(
    lambda callback: callback.data == "reminders_off"
)
async def reminders_off(callback: CallbackQuery):
    cursor.execute(
        """
        INSERT INTO users (user_id, reminders_enabled)
        VALUES (?, 0)
        ON CONFLICT(user_id)
        DO UPDATE SET reminders_enabled = 0
        """,
        (callback.from_user.id,)
    )

    db.commit()

    await callback.message.edit_text("🔕 Напоминания выключены.")
    await callback.answer()


async def reminder_worker():
    while True:
        try:
            now = datetime.now()
            today = days[now.weekday()]

            cursor.execute(
                """
                SELECT
                    schedule.id,
                    schedule.user_id,
                    schedule.subject,
                    schedule.time,
                    schedule.classroom,
                    schedule.reminder_minutes
                FROM schedule
                JOIN users
                ON schedule.user_id = users.user_id
                WHERE schedule.day = ?
                AND users.reminders_enabled = 1
                """,
                (today,)
            )

            lessons = cursor.fetchall()

            for lesson_id, user_id, subject, lesson_time, classroom, reminder_minutes in lessons:
                lesson_datetime = datetime.strptime(
                    f"{now.date()} {lesson_time}",
                    "%Y-%m-%d %H:%M"
                )

                reminder_time = lesson_datetime - timedelta(
                    minutes=reminder_minutes
                )

                if now.strftime("%Y-%m-%d %H:%M") == reminder_time.strftime("%Y-%m-%d %H:%M"):
                    notification_date = now.strftime("%Y-%m-%d")

                    try:
                        cursor.execute(
                            """
                            INSERT INTO notifications
                            (user_id, schedule_id, notification_date)
                            VALUES (?, ?, ?)
                            """,
                            (
                                user_id,
                                lesson_id,
                                notification_date
                            )
                        )

                        db.commit()

                        await bot.send_message(
                            user_id,
                            f"🔔 Напоминание!\n\n"
                            f"Через {reminder_minutes} минут занятие.\n\n"
                            f"📚 {subject}\n"
                            f"⏰ {lesson_time}\n"
                            f"🚪 Кабинет: {classroom}"
                        )

                    except sqlite3.IntegrityError:
                        pass

        except Exception as error:
            print(f"Ошибка reminder_worker: {error}")

        await asyncio.sleep(60)


async def main():
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)

    reminder_task = asyncio.create_task(reminder_worker())

    try:
        await dp.start_polling(bot)
    finally:
        reminder_task.cancel()
        db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())