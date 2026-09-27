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

conn = sqlite3.connect("shopping.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    user_id INTEGER NOT NULL
)
""")

conn.commit()


class AddProduct(StatesGroup):
    waiting_for_name = State()
    waiting_for_quantity = State()


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Добавить товар"),
            KeyboardButton(text="🛒 Мои товары")
        ],
        [
            KeyboardButton(text="🗑 Удалить товар")
        ]
    ],
    resize_keyboard=True
)


@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🛒 Список покупок\n\nВыберите действие:",
        reply_markup=main_keyboard
    )


@router.message(lambda message: message.text == "➕ Добавить товар")
async def add_product(message: Message, state: FSMContext):
    await message.answer("Введите название товара:")
    await state.set_state(AddProduct.waiting_for_name)


@router.message(AddProduct.waiting_for_name)
async def get_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите количество:")
    await state.set_state(AddProduct.waiting_for_quantity)


@router.message(AddProduct.waiting_for_quantity)
async def get_product_quantity(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("Введите количество числом, например: 2")
        return

    data = await state.get_data()
    name = data["name"]
    quantity = int(message.text)

    cursor.execute(
        "INSERT INTO products (name, quantity, user_id) VALUES (?, ?, ?)",
        (name, quantity, message.from_user.id)
    )
    conn.commit()

    await message.answer(
        f"✅ Товар добавлен!\n\n{name} — {quantity} шт.",
        reply_markup=main_keyboard
    )

    await state.clear()


@router.message(lambda message: message.text == "🛒 Мои товары")
async def my_products(message: Message):
    cursor.execute(
        "SELECT id, name, quantity FROM products WHERE user_id = ?",
        (message.from_user.id,)
    )

    products = cursor.fetchall()

    if not products:
        await message.answer("🛒 У вас пока нет товаров.")
        return

    text = "🛒 Ваши товары:\n\n"

    for product_id, name, quantity in products:
        text += f"🆔 {product_id} — {name} — {quantity} шт.\n"

    await message.answer(text)


@router.message(lambda message: message.text == "🗑 Удалить товар")
async def delete_product_list(message: Message):
    cursor.execute(
        "SELECT id, name, quantity FROM products WHERE user_id = ?",
        (message.from_user.id,)
    )

    products = cursor.fetchall()

    if not products:
        await message.answer("🗑 У вас нет товаров для удаления.")
        return

    buttons = []

    for product_id, name, quantity in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"❌ {name} — {quantity} шт.",
                callback_data=f"delete_{product_id}"
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        "Выберите товар, который хотите удалить:",
        reply_markup=keyboard
    )


@router.callback_query(lambda callback: callback.data.startswith("delete_"))
async def delete_product(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])

    cursor.execute(
        "DELETE FROM products WHERE id = ? AND user_id = ?",
        (product_id, callback.from_user.id)
    )
    conn.commit()

    if cursor.rowcount > 0:
        await callback.message.edit_text("✅ Товар удалён.")
    else:
        await callback.message.edit_text("❌ Товар не найден.")

    await callback.answer()


dp.include_router(router)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
