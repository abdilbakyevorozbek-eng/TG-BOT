import asyncio
import os

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)

dp = Dispatcher()
router = Router()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🐍 Python")],
        [KeyboardButton(text="🐧 Linux")],
        [KeyboardButton(text="❓ Помощь")],
    ],
    resize_keyboard=True,
)


@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Привет! 🤖 Я Python-помощник.\n"
        "Выбери нужную кнопку:",
        reply_markup=main_keyboard
    )


@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "Доступные команды:\n\n"
        "/start — запустить бота\n"
        "/help — помощь\n"
        "/python — совет по Python\n"
        "/linux — команда Linux"
    )


@router.message(Command("python"))
async def python_command(message: Message):
    await message.answer(
        "🐍 Совет по Python:\n"
        "Не бойся ошибок. Ошибка показывает, что именно нужно исправить 😄"
    )


@router.message(Command("linux"))
async def linux_command(message: Message):
    await message.answer(
        "🐧 Команда Linux дня:\n\n"
        "ls — показывает файлы и папки в текущей директории."
    )


@router.message(lambda message: message.text == "🐍 Python")
async def python_button(message: Message):
    await python_command(message)


@router.message(lambda message: message.text == "🐧 Linux")
async def linux_button(message: Message):
    await linux_command(message)


@router.message(lambda message: message.text == "❓ Помощь")
async def help_button(message: Message):
    await help_command(message)


@router.message()
async def unknown_message(message: Message):
    await message.answer(
        "🤖 Я этого не понял 😂\n"
        "Нажми одну из кнопок или используй /help."
    )


async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())