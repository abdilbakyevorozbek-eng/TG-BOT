# import asyncio

# async def main():
#     print("Сервер прогрузился. Бот запущен.")
#     await asyncio.sleep(1)

#     print("Сервер прогрузился. Бот запущен.")

# asyncio.run(main())

import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

Bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🤖 Статус")],
        [KeyboardButton(text="😂 Техническая шутка")],
        [KeyboardButton(text="!Помощь")],
    ],
    resize_keyboard=True,
)

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(f"Привет! {message.from_user.first_name}😀\n"
                         f"Как я могу помочь?",
                         reply_markup=main_keyboard)

@router.message(Command("help"))
async def help(message: Message):
    await message.answer("Доступные команды:\n"
                             "/start - Запустить бота\n"
                             "/status - Проверить статус бота\n"
                             "joke - Техническая шутка\n")

@router.message(Command("status"))
async def status(message: Message):
    await message.answer("Бот работает нормально! ✅\n"
                         "Если у вас есть вопросы или проблемы, пожалуйста, свяжитесь с поддержкой.\n" \
                         "Спасибо, что используете нашего бота!")

@router.message(Command("joke"))   
async def joke(message: Message):
    await message.answer("Почему программисты любят темный режим?\n"
                         "Потому что светлый режим слишком яркий для их глаз! 😎\n"
                         "Если у вас есть свои любимые шутки, поделитесь ими с нами!")

@router.message(lambda m: m.text == "🤖 Статус")
async def button_status(message: Message):
    await status(message)

@router.message(lambda m: m.text == "😂 Техническая шутка")
async def button_joke(message: Message):
    await joke(message)

@router.message(lambda m: m.text == "!Помощь")
async def button_help(message: Message):
    await help(message)

@router.message()
async def echo_all(message: Message):
    await message.answer(f"Я не понимаю команду.{message.text}Попробуйте еще раз.")

async def main():
    dp.include_router(router)
    await dp.start_polling(Bot)

if __name__ == "__main__":
    asyncio.run(main())

