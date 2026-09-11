import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router , F
from aiogram.filters import Command
from aiogram.types import(
    Message, CallbackQuery, ReplyKeyboardMarkup, 
    KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
    )

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

main_keyboard = ReplyKeyboardMarkup(             # Основная клавиатура
    keyboard=[
        [KeyboardButton(text="🤖 Статус")],
        [KeyboardButton(text="😂 Техническая шутка")],
        [KeyboardButton(text="!Сервер")],
        [KeyboardButton(text="!Помощь")],
    ],
    resize_keyboard=True
)

server_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(
            text="web_server", callback_data="server:web"
            )],
        [InlineKeyboardButton(
            text="db_server", callback_data="server:db"
            )],
        [InlineKeyboardButton(
            text="backup", callback_data="server:backup"
            )],
        [InlineKeyboardButton(
            text="Назад", callback_data="back_to_main"
            )]
    ]
)

confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text="Сохранить", callback_data="confirm:yes"
        )],
    [InlineKeyboardButton(
        text="Отмена", callback_data="confirm:no"
        )]
    ]
)

Server_Diagnosis = {
    "web_server": "Статус веб-сервера: ✅\nВсе службы работают нормально.",
    "db_server": "Статус базы данных: ✅\nВсе службы работают нормально.",
    "backup": "Статус резервного копирования: ✅\nРезервное копирование выполняется успешно."
}

class AddServerStates(StatesGroup):            # Состояния для добавления сервера FSM
    waiting_for_server_name = State()
    waiting_for_type = State()
    waiting_for_server = State()

@router.message(Command("start"))               # Команда /start Базовая
async def start(message: Message):
    await message.answer(
        f"Привет! {message.from_user.first_name}😀\n"
        f"Как я могу помочь?",
        reply_markup=main_keyboard
    )

@router.message(Command("help"))
async def help(message: Message):
    await message.answer(
        "Доступные команды:\n"
        "/start - Запустить бота\n"
        "/status - Проверить статус бота\n"
        "/joke - Техническая шутка\n"
        "/servers - Проверить статус серверов\n"
        "/add_server - Добавить сервер\n"
        "/cancel - Отменить текущее действие\n"
    )

@router.message(Command("status"))
async def status(message: Message):
    await message.answer(
        "web_server работает нормально! ✅\n"
        "db_server работает нормально! ✅\n"
        "backup выполняется успешно! ✅\n"
        "Если у вас есть вопросы или проблемы, пожалуйста, свяжитесь с поддержкой.\n"
        "Спасибо, что используете нашего бота!"
    )

@router.message(Command("joke"))
async def joke(message: Message):
    await message.answer(
        "почему программисты любят темный режим?\n"
        "Потому что светлый режим вызывает у них исключение!"
        "если у вас есть свои любимые шутки, поделитесь ими с нами!"
    )

@router.message(Command("cencel"))
async def cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активного действия для отмены.")
        return

    await state.clear()
    await message.answer("Текущее действие отменено.")

# Кнопки

@router.message(F.text == "🤖 Статус")
async def button_status(message: Message):
    await status(message)

@router.message(F.text == "😂 Техническая шутка")
async def button_joke(message: Message):
    await joke(message)

@router.message(F.text == "!Помощь")
async def button_help(message: Message):
    await help(message)

@router.message(F.text == "!Сервер")
async def button_server(message: Message):
    await servers(message)
#inline Кнопки

@router.message(Command("servers"))
async def servers(message: Message):
    await message.answer(
        "Выберите сервер для проверки статуса:",
        reply_markup=server_keyboard
    )

@router.callback_query(F.data.startswith("server:"))
async def db_server_diagnosis(callback: CallbackQuery):
    servers_key = callback.data.split(":")[1]
    text = Server_Diagnosis.get(servers_key, "Неизвестный сервер.")
    await callback.message.edit_text(text)
    await callback.answer()

#FSM- диалог для добавления сервера

@router.message(Command("add_server"))
async def add_server(message: Message, state: FSMContext):
    await message.answer("Введите имя сервера:")
    await state.set_state(AddServerStates.waiting_for_server_name)

@router.message(AddServerStates.waiting_for_server_name)
async def process_server_name(message: Message, state: FSMContext):
    server_name = message.text
    await state.update_data(server_name=server_name)
    await message.answer("Введите тип сервера (например, web, db, backup):")
    await state.set_state(AddServerStates.waiting_for_type)

@router.message(AddServerStates.waiting_for_type)
async def process_server_type(message: Message, state: FSMContext):
    await state.update_data(server_type=message.text)
    await message.answer("Введите адрес сервера:")
    await state.set_state(AddServerStates.waiting_for_server)

@router.message(AddServerStates.waiting_for_server)
async def process_server_status(message: Message, state: FSMContext):
    data = await state.update_data(server_address=message.text)
    await message.answer(
        f"Вы ввели следующие данные:\n"
        f"Имя сервера: {data['server_name']}\n"
        f"Тип сервера: {data['server_type']}\n"
        f"Адрес сервера: {data['server_address']}\n"
        "Сохранить эти данные?",
        reply_markup=confirm_keyboard
    )

@router.callback_query(F.data.startswith("confirm:"))
async def confirm_data(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Данные сохранены успешно✅")

@router.callback_query(F.data == "confirm_cancel")
async def cb_confirm_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Добавление отменено❌")
    await callback.answer()

@router.message()
async def echo_all(message: Message):
    await message.answer(f"Я не понимаю команду: {message.text}. Попробуйте еще раз.")

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
