
import asyncio
import os

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN1")

bot = Bot(token=BOT_TOKEN)

dp = Dispatcher()
router = Router()
@router.message(Command("start"))
async def start(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🐍 Python",
                    callback_data="python"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗄 SQL",
                    callback_data="sql"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🐧 Linux",
                    callback_data="linux"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❓ Помощь",
                    callback_data="help"
                )
            ]
        ]
    )

    await message.answer(
        "Привет! � Я Python-помощник.\n"
        "Выбери нужную кнопку:",
        reply_markup=keyboard
    )


@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "ℹ️ Помощь:\n\n"
        "🐍 Python — язык программирования.\n"
        "🗄 SQL — язык для работы с базами данных.\n"
        "🐧 Linux — операционная система."
    )


@router.callback_query()
async def callback_handler(callback: CallbackQuery):

    if callback.data == "python":
        await callback.message.answer(
            "🐍 Python — язык программирования."
        )

    elif callback.data == "sql":
        await callback.message.answer(
            "🗄 SQL — язык для работы с базами данных."
        )

    elif callback.data == "linux":
        await callback.message.answer(
            "🐧 Linux — операционная система."
        )

    elif callback.data == "help":
        await callback.message.answer(
            "ℹ️ Помощь:\n\n"
            "🐍 Python — язык программирования.\n"
            "🗄 SQL — язык для работы с базами данных.\n"
            "🐧 Linux — операционная система."
        )

    await callback.answer()


@router.message()
async def unknown_message(message: Message):
    await message.answer(
        "🤖 Я этого не понял 😂\n"
        "Нажми /start или используй /help."
    )


async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
