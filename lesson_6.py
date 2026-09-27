import asyncio
import os
import sqlite3

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN1")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

conn = sqlite3.connect("schedule.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day TEXT NOT NULL,
    subject TEXT NOT NULL,
    time TEXT NOT NULL,
    classroom TEXT NOT NULL
)
""")

conn.commit()


class AddLesson(StatesGroup):
    waiting_for_day = State()
    waiting_for_subject = State()
    waiting_for_time = State()
    waiting_for_classroom = State()


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Добавить занятие"),
            KeyboardButton(text="📚 Всё расписание")
        ],
        [
            KeyboardButton(text="📅 Выбрать день"),
            KeyboardButton(text="🗑 Удалить занятие")
        ]
    ],
    resize_keyboard=True
)


days_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Понедельник", callback_data="day_Понедельник"),
            InlineKeyboardButton(text="Вторник", callback_data="day_Вторник")
        ],
        [
            InlineKeyboardButton(text="Среда", callback_data="day_Среда"),
            InlineKeyboardButton(text="Четверг", callback_data="day_Четверг")
        ],
        [
            InlineKeyboardButton(text="Пятница", callback_data="day_Пятница"),
            InlineKeyboardButton(text="Суббота", callback_data="day_Суббота")
        ],
        [
            InlineKeyboardButton(text="Воскресенье", callback_data="day_Воскресенье")
        ]
    ]
)


@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "📚 Расписание\n\nВыберите действие:",
        reply_markup=main_keyboard
    )


@router.message(lambda message: message.text == "➕ Добавить занятие")
async def add_lesson(message: Message, state: FSMContext):
    await message.answer(
        "Введите день недели:\n\n"
        "Понедельник\n"
        "Вторник\n"
        "Среда\n"
        "Четверг\n"
        "Пятница\n"
        "Суббота\n"
        "Воскресенье"
    )
    await state.set_state(AddLesson.waiting_for_day)


@router.message(AddLesson.waiting_for_day)
async def get_day(message: Message, state: FSMContext):
    days = [
        "Понедельник",
        "Вторник",
        "Среда",
        "Четверг",
        "Пятница",
        "Суббота",
        "Воскресенье"
    ]

    if message.text not in days:
        await message.answer("Выберите день из списка.")
        return

    await state.update_data(day=message.text)
    await message.answer("Введите название предмета:")
    await state.set_state(AddLesson.waiting_for_subject)


@router.message(AddLesson.waiting_for_subject)
async def get_subject(message: Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await message.answer("Введите время, например: 09:00:")
    await state.set_state(AddLesson.waiting_for_time)


@router.message(AddLesson.waiting_for_time)
async def get_time(message: Message, state: FSMContext):
    await state.update_data(time=message.text)
    await message.answer("Введите номер кабинета:")
    await state.set_state(AddLesson.waiting_for_classroom)


@router.message(AddLesson.waiting_for_classroom)
async def get_classroom(message: Message, state: FSMContext):
    data = await state.get_data()

    cursor.execute(
        """
        INSERT INTO schedule (day, subject, time, classroom)
        VALUES (?, ?, ?, ?)
        """,
        (
            data["day"],
            data["subject"],
            data["time"],
            message.text
        )
    )

    conn.commit()

    await message.answer(
        f"✅ Занятие добавлено!\n\n"
        f"📅 {data['day']}\n"
        f"📚 {data['subject']}\n"
        f"⏰ {data['time']}\n"
        f"🚪 Кабинет: {message.text}",
        reply_markup=main_keyboard
    )

    await state.clear()


@router.message(lambda message: message.text == "📚 Всё расписание")
async def show_schedule(message: Message):
    cursor.execute(
        "SELECT id, day, subject, time, classroom FROM schedule ORDER BY id"
    )

    lessons = cursor.fetchall()

    if not lessons:
        await message.answer("📚 Расписание пока пустое.")
        return

    text = "📚 Всё расписание:\n\n"

    for lesson_id, day, subject, time, classroom in lessons:
        text += (
            f"🆔 {lesson_id}\n"
            f"📅 {day}\n"
            f"📚 {subject}\n"
            f"⏰ {time}\n"
            f"🚪 Кабинет: {classroom}\n\n"
        )

    await message.answer(text)


@router.message(lambda message: message.text == "📅 Выбрать день")
async def choose_day(message: Message):
    await message.answer(
        "📅 Выберите день:",
        reply_markup=days_keyboard
    )


@router.callback_query(lambda callback: callback.data.startswith("day_"))
async def show_day(callback: CallbackQuery):
    day = callback.data.replace("day_", "")

    cursor.execute(
        """
        SELECT subject, time, classroom
        FROM schedule
        WHERE day = ?
        ORDER BY time
        """,
        (day,)
    )

    lessons = cursor.fetchall()

    if not lessons:
        await callback.message.edit_text(
            f"📅 {day}\n\nЗанятий нет."
        )
        await callback.answer()
        return

    text = f"📅 {day}\n\n"

    for subject, time, classroom in lessons:
        text += (
            f"📚 {subject}\n"
            f"⏰ {time}\n"
            f"🚪 Кабинет: {classroom}\n\n"
        )

    await callback.message.edit_text(text)
    await callback.answer()


@router.message(lambda message: message.text == "🗑 Удалить занятие")
async def delete_lesson_list(message: Message):
    cursor.execute(
        "SELECT id, day, subject, time, classroom FROM schedule ORDER BY id"
    )

    lessons = cursor.fetchall()

    if not lessons:
        await message.answer("🗑 Расписание пустое.")
        return

    buttons = []

    for lesson_id, day, subject, time, classroom in lessons:
        buttons.append([
            InlineKeyboardButton(
                text=f"❌ {day} — {subject} — {time}",
                callback_data=f"delete_{lesson_id}"
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        "🗑 Выберите занятие для удаления:",
        reply_markup=keyboard
    )


@router.callback_query(lambda callback: callback.data.startswith("delete_"))
async def delete_lesson(callback: CallbackQuery):
    lesson_id = int(callback.data.split("_")[1])

    cursor.execute(
        "DELETE FROM schedule WHERE id = ?",
        (lesson_id,)
    )

    conn.commit()

    if cursor.rowcount > 0:
        await callback.message.edit_text("✅ Занятие удалено.")
    else:
        await callback.message.edit_text("❌ Занятие не найдено.")

    await callback.answer()


dp.include_router(router)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
