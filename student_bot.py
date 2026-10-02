import asyncio
import os
import sqlite3

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN2")

if not BOT_TOKEN:
    raise ValueError(" BOT_TOKEN ")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

conn = sqlite3.connect("students.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    city TEXT NOT NULL
)
""")

conn.commit()


class AddStudent(StatesGroup):
    name = State()
    age = State()
    city = State()


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить студента"),
         KeyboardButton(text="📋 Список студентов")],
        [KeyboardButton(text="❓ Answers"),
         KeyboardButton(text="ℹ️ Help")]
    ],
    resize_keyboard=True
)

@router.message(F.text == "ℹ️ Help")
async def help_button(message: Message):
    await message.answer(
        "Я умею:\n"
        "➕ Добавлять студентов\n"
        "📋 Показывать список студентов\n"
        "🗑 Удалять студентов"
    )

@router.message(F.text == "❓ Answers")
async def answers_button(message: Message):
    text = "\n\n".join(
        f"{question}. {answer}"
        for question, answer in answers.items()
    )
    await message.answer(text)

@router.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Привет! Я бот для управления студентами.",
        reply_markup=main_keyboard
    )


@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "Я умею добавлять, показывать и удалять студентов."
    )


@router.message(F.text == "➕ Добавить студента")
async def add_student(message: Message, state: FSMContext):
    await state.set_state(AddStudent.name)
    await message.answer("Введите имя студента:")


@router.message(AddStudent.name)
async def enter_name(message: Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer("Введите имя текстом:")
        return

    await state.update_data(name=message.text.strip())
    await state.set_state(AddStudent.age)
    await message.answer("Введите возраст студента:")


@router.message(AddStudent.age)
async def enter_age(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("Возраст должен быть целым числом. Попробуйте ещё раз:")
        return

    age = int(message.text)

    if age < 1 or age > 120:
        await message.answer("Введите возраст от 1 до 120:")
        return

    await state.update_data(age=age)
    await state.set_state(AddStudent.city)
    await message.answer("Введите город студента:")


@router.message(AddStudent.city)
async def enter_city(message: Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer("Введите название города:")
        return

    data = await state.get_data()

    cursor.execute(
        "INSERT INTO students (name, age, city) VALUES (?, ?, ?)",
        (data["name"], data["age"], message.text.strip())
    )
    conn.commit()

    await message.answer(
        f"✅ Студент добавлен!\n\n"
        f"Имя: {data['name']}\n"
        f"Возраст: {data['age']}\n"
        f"Город: {message.text.strip()}",
        reply_markup=main_keyboard
    )

    await state.clear()


@router.message(F.text == "📋 Список студентов")
async def show_students(message: Message):
    cursor.execute("SELECT id, name, age, city FROM students")
    students = cursor.fetchall()

    if not students:
        await message.answer("Список студентов пока пуст.")
        return

    for student_id, name, age, city in students:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🗑 Удалить",
                        callback_data=f"delete_{student_id}"
                    )
                ]
            ]
        )

        await message.answer(
            f"👤 Имя: {name}\n"
            f"🎂 Возраст: {age}\n"
            f"🏙 Город: {city}",
            reply_markup=keyboard
        )


@router.callback_query(F.data.startswith("delete_"))
async def delete_student(callback: CallbackQuery):
    student_id = int(callback.data.split("_")[1])

    cursor.execute(
        "DELETE FROM students WHERE id = ?",
        (student_id,)
    )
    conn.commit()

    if cursor.rowcount > 0:
        await callback.message.edit_text("✅ Студент удалён.")
        await callback.answer("Студент удалён")
    else:
        await callback.answer("Студент уже удалён", show_alert=True)


answers = {
    1: "Linux — это операционная система, которая используется на компьютерах и серверах.",
    2: "Aiogram — библиотека Python для создания Telegram-ботов.",
    3: "Callback — это обработка нажатия Inline-кнопки, которая позволяет боту выполнить нужное действие.",
    4: "FSM — механизм, который помогает боту запоминать этап диалога, например имя, возраст и город.",
    5: "База данных — организованное хранилище информации.",
    6: "SQLite — лёгкая база данных, которая хранится в файле и не требует отдельного сервера.",
    7: "INSERT добавляет данные, SELECT получает данные, UPDATE изменяет данные, DELETE удаляет данные.",
    8: "JOIN — SQL-команда для объединения данных из нескольких связанных таблиц.",
    9: "Inline-кнопки позволяют выполнять действия прямо под сообщением Telegram.",
    10: "Python содержит код бота, aiogram обеспечивает взаимодействие с Telegram, а SQLite хранит данные студентов."
}


@router.message(Command("answers"))
async def show_answers(message: Message):
    text = "\n\n".join(
        f"{question}. {answer}"
        for question, answer in answers.items()
    )
    await message.answer(text)


async def main():
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    finally:
        conn.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
