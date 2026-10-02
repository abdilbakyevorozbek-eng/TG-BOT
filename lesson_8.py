import asyncio
import os
import sqlite3

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
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
    raise ValueError("Добавьте BOT_TOKEN в файл .env")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    date TEXT NOT NULL
)
""")

conn.commit()


class AddExpense(StatesGroup):
    name = State()
    amount = State()
    category = State()
    date = State()


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить расход"),
         KeyboardButton(text="📋 Все расходы")],
        [KeyboardButton(text="🏷 По категориям"),
         KeyboardButton(text="🗑 Удалить расход")],
        [KeyboardButton(text="💰 Общая сумма")]
    ],
    resize_keyboard=True
)


categories_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🍔 Еда",
                callback_data="category_Еда"
            ),
            InlineKeyboardButton(
                text="🚕 Транспорт",
                callback_data="category_Транспорт"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎮 Развлечения",
                callback_data="category_Развлечения"
            ),
            InlineKeyboardButton(
                text="🛍 Покупки",
                callback_data="category_Покупки"
            )
        ],
        [
            InlineKeyboardButton(
                text="📚 Учёба",
                callback_data="category_Учёба"
            ),
            InlineKeyboardButton(
                text="📦 Другое",
                callback_data="category_Другое"
            )
        ]
    ]
)


@router.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "💰 Добро пожаловать в бот учета расходов!",
        reply_markup=main_keyboard
    )


@router.message(F.text == "➕ Добавить расход")
async def add_expense(message: Message, state: FSMContext):
    await state.set_state(AddExpense.name)
    await message.answer("Введите название покупки:")


@router.message(AddExpense.name)
async def expense_name(message: Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer("Введите название покупки:")
        return

    await state.update_data(name=message.text.strip())
    await state.set_state(AddExpense.amount)
    await message.answer("Введите сумму:")


@router.message(AddExpense.amount)
async def expense_amount(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Введите сумму числом:")
        return

    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Введите сумму числом, например: 250")
        return

    if amount <= 0:
        await message.answer("Сумма должна быть больше 0:")
        return

    await state.update_data(amount=amount)
    await state.set_state(AddExpense.category)

    await message.answer(
        "Выберите категорию:",
        reply_markup=categories_keyboard
    )


@router.callback_query(AddExpense.category, F.data.startswith("category_"))
async def expense_category(
    callback: CallbackQuery,
    state: FSMContext
):
    category = callback.data.replace("category_", "")

    await state.update_data(category=category)
    await state.set_state(AddExpense.date)

    await callback.message.edit_text(
        f"Выбрана категория: {category}\n\n"
        "Введите дату покупки в формате ДД.ММ.ГГГГ:"
    )

    await callback.answer()


@router.message(AddExpense.date)
async def expense_date(message: Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer("Введите дату, например: 01.10.2026")
        return

    data = await state.get_data()

    cursor.execute(
        """
        INSERT INTO expenses (name, amount, category, date)
        VALUES (?, ?, ?, ?)
        """,
        (
            data["name"],
            data["amount"],
            data["category"],
            message.text.strip()
        )
    )

    conn.commit()

    await message.answer(
        f"✅ Расход добавлен!\n\n"
        f"Покупка: {data['name']}\n"
        f"Сумма: {data['amount']:.2f}\n"
        f"Категория: {data['category']}\n"
        f"Дата: {message.text.strip()}",
        reply_markup=main_keyboard
    )

    await state.clear()


@router.message(F.text == "📋 Все расходы")
async def show_expenses(message: Message):
    cursor.execute(
        "SELECT id, name, amount, category, date FROM expenses"
    )

    expenses = cursor.fetchall()

    if not expenses:
        await message.answer("📭 Расходов пока нет.")
        return

    text = "📋 Все расходы:\n\n"

    for expense_id, name, amount, category, date in expenses:
        text += (
            f"🆔 {expense_id}\n"
            f"🛒 {name}\n"
            f"💵 {amount:.2f}\n"
            f"🏷 {category}\n"
            f"📅 {date}\n\n"
        )

    await message.answer(text)


@router.message(F.text == "🏷 По категориям")
async def choose_category(message: Message):
    await message.answer(
        "Выберите категорию:",
        reply_markup=categories_keyboard
    )


@router.callback_query(F.data.startswith("category_"))
async def show_category(callback: CallbackQuery):
    category = callback.data.replace("category_", "")

    cursor.execute(
        """
        SELECT id, name, amount, date
        FROM expenses
        WHERE category = ?
        """,
        (category,)
    )

    expenses = cursor.fetchall()

    if not expenses:
        await callback.message.edit_text(
            f"📭 В категории «{category}» расходов нет."
        )
        await callback.answer()
        return

    text = f"🏷 Расходы категории «{category}»:\n\n"

    for expense_id, name, amount, date in expenses:
        text += (
            f"🆔 {expense_id}\n"
            f"🛒 {name}\n"
            f"💵 {amount:.2f}\n"
            f"📅 {date}\n\n"
        )

    await callback.message.edit_text(text)
    await callback.answer()


@router.message(F.text == "🗑 Удалить расход")
async def delete_expense(message: Message):
    cursor.execute(
        "SELECT id, name, amount FROM expenses"
    )

    expenses = cursor.fetchall()

    if not expenses:
        await message.answer("📭 Расходов для удаления нет.")
        return

    buttons = []

    for expense_id, name, amount in expenses:
        buttons.append([
            InlineKeyboardButton(
                text=f"🗑 {name} — {amount:.2f}",
                callback_data=f"delete_{expense_id}"
            )
        ])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    await message.answer(
        "Выберите расход для удаления:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("delete_"))
async def delete_expense_callback(callback: CallbackQuery):
    expense_id = int(callback.data.replace("delete_", ""))

    cursor.execute(
        "DELETE FROM expenses WHERE id = ?",
        (expense_id,)
    )

    conn.commit()

    await callback.message.edit_text("✅ Расход удалён.")
    await callback.answer("Расход удалён")


@router.message(F.text == "💰 Общая сумма")
async def total_expenses(message: Message):
    cursor.execute(
        "SELECT SUM(amount) FROM expenses"
    )

    result = cursor.fetchone()[0]

    if result is None:
        result = 0

    await message.answer(
        f"💰 Общая сумма расходов: {result:.2f}"
    )


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
