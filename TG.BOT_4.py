import asyncio
import os
import random

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import (Message, ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)

router = Router()

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎬 Случайный фильм"),
        KeyboardButton(text="⭐ Выбор фильмов")],
        [KeyboardButton(text="ℹ️ Помощь")]
    ],
    resize_keyboard=True
)

anime_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Наруто"),
        KeyboardButton(text="Атака титанов")],
        [KeyboardButton(text="Клинок рассекающий демонов"),
        KeyboardButton(text="Ван Пис")],
        [KeyboardButton(text="Блич"),
        KeyboardButton(text="Тетрадь смерти")],
        [KeyboardButton(text="Магическая битва"),
        KeyboardButton(text="Хантер × Хантер")],
        [KeyboardButton(text="Моя геройская академия")]
    ],
    resize_keyboard=True
)

movies = [
    "Наруто",
    "Атака титанов",
    "Клинок рассекающий демонов",
    "Ван Пис",
    "Блич",
    "Тетрадь смерти",
    "Магическая битва",
    "Хантер × Хантер",
    "Моя геройская академия",
]

anime_data = {
    "Наруто": {
        "photo": "https://cdn.europosters.eu/image/1300/218002.jpg",
        "watch": "https://anime.dizord.ru/catalog"
    },
    "Атака титанов": {
        "photo": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTBkM4-vewu_"
        "BOfsw27qFtuk_v2v6L5JSg2VC0AdLWR67Tq-HNvZA&s&ec=121966374",
        "watch": "https://anime.dizord.ru/catalog"
    },
    "Клинок рассекающий демонов": {
        "photo": "https://encrypted-tbn0.gstatic.com/images?q="
        "tbn:ANd9GcQM6Z17Ot00mlWwm_RCZl1EGJmDW5cgfXTVG6ay9K-Ypg&s=10",
        "watch": "https://anime.dizord.ru/catalog"
    },
    "Ван Пис": {
        "photo": "https://encrypted-tbn0.gstatic.com/images?q=t"
        "bn:ANd9GcQ17c8Oy-XnK_YgirBXFUHBlc-7G__1WNry6YY83WHEYw&s=10",
        "watch": "https://anime.dizord.ru/catalog"
    },
    "Блич": {
        "photo": "https://encrypted-tbn0.gstatic.com/images?q=t"
        "bn:ANd9GcTwDuDgVaT1fxUv21eq3dBzwgvbqpNRJBt3P2ERy1HkpOaUvnlGs8KU9Rv_&s=10",
        "watch": "https://anime.dizord.ru/catalog"
    },
    "Тетрадь смерти": {
        "photo": "https://cdn.kanobu.ru/anime/anime/a88d6a18-0699-4d24-ad30-c37bbd1da72f.webp",
        "watch": "https://anime.dizord.ru/catalog"
    },
    "Магическая битва": {
        "photo": "https://encrypted-tbn0.gstatic.com/images?q=t"
        "bn:ANd9GcQmuTONDaP4SGSo_OrSLBK0pZ2NxupHfFdfM7hEU3VfTA&s",
        "watch": "https://anime.dizord.ru/catalog"
    },
    "Хантер × Хантер": {
        "photo": "https://encrypted-tbn0.gstatic.com/images?q="
        "tbn:ANd9GcS6lVgKk23GzNbLkEFvPsNs264FjYHt7kyWNLCnk4o7Zw&s=10",
        "watch": "https://anime.dizord.ru/catalog"
    },
    "Моя геройская академия": {
        "photo": "https://encrypted-tbn0.gstatic.com/images?q="
        "tbn:ANd9GcSa1YAMYIs5cCz67kRFNQa9LrYc7NMq6wUfGcc-4SXU_g&s=10",
        "watch": "https://anime.dizord.ru/catalog"
    }
}

def watch_keyboard(url):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="▶️ Смотреть",
                    url=url
                )
            ]
        ]
    )

@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
    "🎬 Привет! Добро пожаловать в Кино-бот!\n\n"
    "🍿 Здесь ты можешь найти случайный фильм "
    "и посмотреть топ популярных фильмов.\n\n"
    "Выбери действие ниже 👇",
    reply_markup=main_keyboard
)
    
@router.message(Command("help"))
async def help(message: Message):
    await message.answer(
        "Доступные команды:\n"
        '/start - Запустить бота\n'
        '/help - Помощь\n'
        "/random_movie - Получить случайный фильм\n"
        "/top_movies - Посмотреть выбор фильмов\n"
        "/cancel - Отменить текущее действие\n"
        "Если у вас есть вопросы или предложения, пожалуйста,\n"
        "свяжитесь с <a href=\"https://t.me/abdy1bakiev\">Telegram</a>.",
        parse_mode="HTML"
    )

@router.message(Command("random_movie"))
async def random_movie(message: Message):
    title = random.choice(list(anime_data.keys()))
    anime = anime_data[title]

    await message.answer_photo(
        photo=anime["photo"],
        caption=f"🎬 {title}\n\nНажми кнопку ниже:",
        reply_markup=watch_keyboard(anime["watch"])
    )

@router.message(Command("top_movies"))
async def top_movies(message: Message):
    top_movies_list = "\n".join([f"{i+1}. {movie}" for i, movie in enumerate(movies)])
    await message.answer(
        f"⭐ Выбор фильмов:\n{top_movies_list}"
    )
    

@router.message(lambda m: m.text == "🎬 Случайный фильм")
async def button_random_movie(message: Message):
    title = random.choice(list(anime_data.keys()))
    anime = anime_data[title]

    await message.answer_photo(
        photo=anime["photo"],
        caption=f"🎬 {title}\n\nНажми кнопку ниже:",
        reply_markup=watch_keyboard(anime["watch"])
    )

@router.message(lambda m: m.text == "⭐ Выбор фильмов")
async def button_top_movies(message: Message):
    await message.answer(
        "⭐ Выбери аниме:",
        reply_markup=anime_keyboard
    )

@router.message(lambda m: m.text in anime_data)
async def button_anime_info(message: Message):
    title = message.text
    anime = anime_data[title]

    await message.answer_photo(
        photo=anime["photo"],
        caption=f"{title}\n\nНажми кнопку ниже:",
        reply_markup=watch_keyboard(anime["watch"])
    )

@router.message(lambda m: m.text == "ℹ️ Помощь")
async def button_help(message: Message):
    await help(message)

@router.message(lambda m: m.text.lower() == "привет")
async def hello(message: Message):
    await message.answer(
        "Привет! Рад тебе видеть! 🎬"
    )

@router.message(lambda m: m.text.lower() == "спасибо")
async def thanks(message: Message):
    await message.answer(
        "Пожалуйста! Всегда рад помочь 😊"
    )

@router.message(Command("cancel"))
async def cancel(message: Message):
    await message.answer(
        "Действие отменено.",
    )

@router.message()
async def unknown_message(message: Message):
    await message.answer(
        "Извини, я не понимаю эту команду. 😅\n"
        "Попробуй использовать кнопки ниже или введи /help для помощи.\n"
        "Используй команды /start, /help, /random или /top.\n"
        "Если у тебя есть предложения или вопросы,\n"
        "свяжись с <a href=\"https://t.me/abdy1bakiev\">@abdy1bakiev</a>.",
    )

async def main():
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())