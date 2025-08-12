import logging
import asyncio 
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from database import Database
import keyboards as kb
from aiogram.utils import executor

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token="7444573816:AAFAU2EckrSQE_rQjvBtI8r6ObT4NoApHnw")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db = Database('database.db')

# Состояния для FSM
class Form(StatesGroup):
    waiting_for_project_type = State()
    waiting_for_channel_info = State()
    waiting_for_bot_info = State()
    waiting_for_mini_app_info = State()
    waiting_for_theme = State()
    waiting_for_payment_method = State()
    waiting_for_complaint = State()

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    welcome_text = """
    Добро пожаловать в наш агрегатор!

    1. Ищи любые каналы, боты или мини-приложения по нужной тебе тематике.
    2. Подключи свой канал к нам и получай бесплатный трафик.
    3. Выполняй задания и выводи свой канал в топ.
    """
    await message.answer(welcome_text, reply_markup=kb.main_menu())

# Обработчик главного меню
@dp.message_handler(text="Главная страница")
async def main_page(message: types.Message):
    await message.answer(
        "Выберите тип контента для поиска:",
        reply_markup=kb.content_type_menu()
    )

# Обработчик выбора типа контента
@dp.callback_query_handler(lambda c: c.data in ['channels', 'bots', 'mini_apps'])
async def process_content_type(callback_query: types.CallbackQuery):
    content_type = callback_query.data
    if content_type == 'channels':
        themes = db.get_channel_themes()
    elif content_type == 'bots':
        themes = db.get_bot_themes()
    else:
        themes = ["Все подряд"]  # Для мини-приложений
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "Выберите тематику:",
        reply_markup=kb.generate_themes_menu(themes, content_type)
    )

# Обработчик выбора тематики
@dp.callback_query_handler(lambda c: c.data.startswith('theme_'))
async def process_theme(callback_query: types.CallbackQuery):
    _, content_type, theme = callback_query.data.split('_')
    items = db.get_items_by_theme(content_type, theme)
    
    # Формируем сообщение с премиум и обычными позициями
    message_text = "🏆 <b>Премиум место:</b>\n\n"
    premium_item = next((item for item in items if item['is_premium']), None)
    
    if premium_item:
        message_text += f"✨ <b>{premium_item['name']}</b>\n"
        message_text += f"📌 Тематика: {premium_item['theme']}\n"
        message_text += f"🔥 Популярный пост: {premium_item['popular_post']}\n"
        message_text += f"🔗 Ссылка: {premium_item['link']}\n\n"
        message_text += f"❤️ Лайков: {premium_item['likes']}\n\n"
    
    message_text += "<b>Другие проекты:</b>\n\n"
    
    for item in items[:10]:  # Первые 10 обычных проектов
        if not item['is_premium']:
            message_text += f"📌 <b>{item['name']}</b>\n"
            message_text += f"🏷 Тематика: {item['theme']}\n"
            message_text += f"🔗 Ссылка: {item['link']}\n"
            message_text += f"❤️ Лайков: {item['likes']}\n\n"
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        message_text,
        parse_mode='HTML',
        reply_markup=kb.items_list_keyboard(items, content_type)
    )

# Обработчик кнопки "Мой проект"
@dp.message_handler(text="Мой проект")
async def my_project(message: types.Message):
    await message.answer(
        "Выберите тип проекта для подключения:",
        reply_markup=kb.project_type_menu()
    )


# Обработчик выбора типа проекта
@dp.message_handler(state=Form.waiting_for_project_type)
async def process_project_type(message: types.Message, state: FSMContext):
    if message.text == 'Канал':
        await message.answer(
            "Для подключения канала:\n"
            "1. Добавьте нашего бота в администраторы вашего канала\n"
            "2. Отправьте ссылку на ваш канал",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await Form.waiting_for_channel_info.set()
    elif message.text == 'Бот':
        await message.answer(
            "Для подключения бота:\n"
            "1. Отправьте ссылку на вашего бота\n"
            "2. Или отправьте токен бота (если хотите интегрировать нашу рекламу)",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await Form.waiting_for_bot_info.set()
    elif message.text == 'Мини-приложение':
        await message.answer(
            "Для подключения мини-приложения:\n"
            "1. Отправьте ссылку на ваше мини-приложение\n"
            "2. Если есть задания для пользователей, опишите их",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await Form.waiting_for_mini_app_info.set()
    else:
        await message.answer("Пожалуйста, выберите тип проекта из предложенных вариантов")

# Обработчик подключения канала
@dp.message_handler(state=Form.waiting_for_channel_info)
async def process_channel_info(message: types.Message, state: FSMContext):
    # Здесь должна быть проверка, что бот добавлен в админы канала
    await state.update_data(project_type='channel', link=message.text)
    await message.answer("Выберите тематику канала:", reply_markup=kb.themes_menu)
    await Form.waiting_for_theme.set()

# Обработчик выбора тематики
@dp.message_handler(state=Form.waiting_for_theme)
async def process_theme_selection(message: types.Message, state: FSMContext):
    await state.update_data(theme=message.text)
    await message.answer(
        "Выберите способ размещения:",
        reply_markup=kb.payment_method_menu
    )
    await Form.waiting_for_payment_method.set()

# Обработчик выбора способа оплаты
@dp.message_handler(state=Form.waiting_for_payment_method)
async def process_payment_method(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    if message.text == 'Бесплатно (за выполнение условий)':
        # Проверяем, есть ли у пользователя достаточно звезд
        stars = db.get_user_stars(message.from_user.id)
        if stars >= 10:
            db.add_project(
                user_id=message.from_user.id,
                project_type=user_data['project_type'],
                link=user_data['link'],
                theme=user_data['theme'],
                is_premium=True,
                stars_cost=10
            )
            db.update_user_stars(message.from_user.id, -10)
            await message.answer(
                "Ваш проект добавлен в премиум-размещение!",
                reply_markup=kb.main_menu
            )
        else:
            await message.answer(
                "У вас недостаточно звезд для премиум-размещения. "
                "Вы можете выполнить задания, чтобы получить звезды.",
                reply_markup=kb.main_menu
            )
    elif message.text == 'Платно':
        await message.answer(
            "Оплатите размещение по ссылке: [payment_link]\n"
            "После оплаты ваш проект будет активирован.",
            reply_markup=kb.main_menu
        )
    else:
        await message.answer("Пожалуйста, выберите вариант из предложенных")
        return
    
    await state.finish()

# Обработчик кнопки "Банер AdGram"
@dp.message_handler(text="Банер AdGram")
async def adgram_banner(message: types.Message):
    tasks = db.get_available_tasks(message.from_user.id)
    if tasks:
        await message.answer(
            "Выполняйте задания и получайте звезды:",
            reply_markup=kb.tasks_keyboard()
        )
    else:
        await message.answer("У вас нет доступных заданий")
    

@dp.message_handler(text="Личный профиль")
async def personal_profile(message: types.Message):
    user_info = db.get_user_info(message.from_user.id)
    if user_info:
        await message.answer(
            f"👤 Ваш профиль\n\n"
            f"⭐ Звезды: {user_info['stars']}\n"
            f"💰 Баланс: {user_info['balance']} руб.\n"
            f"📊 Проектов: {user_info['projects_count']}",
            reply_markup=kb.profile_menu()
        )
    else:
        await message.answer("Профиль не найден")

@dp.callback_query_handler(lambda c: c.data.startswith("task_"))
async def process_task(callback_query: types.CallbackQuery):
    task_type = callback_query.data.split("_")[1]
    db.complete_task(callback_query.from_user.id, task_type)
    await bot.answer_callback_query(callback_query.id, "Задание выполнено!")
    await bot.send_message(
        callback_query.from_user.id,
        f"Вы получили {'5' if task_type == 'banner' else '3' if task_type == 'subscribe' else '10'}🌟!"
    )

# Обработчик лайков
@dp.callback_query_handler(lambda c: c.data.startswith('like_'))
async def process_like(callback_query: types.CallbackQuery):
    _, item_id = callback_query.data.split('_')
    db.add_like(item_id)
    await bot.answer_callback_query(callback_query.id, "❤️ Ваш лайк учтён!")

# Обработчик жалоб
@dp.callback_query_handler(lambda c: c.data.startswith('report_'))
async def process_report(callback_query: types.CallbackQuery):
    _, item_id = callback_query.data.split('_')
    await bot.send_message(
        callback_query.from_user.id,
        "Опишите проблему с этим проектом:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await Form.waiting_for_complaint.set()
    await state.update_data(item_id=item_id)

@dp.message_handler(text="Канал")
async def adgram_banner(message: types.Message):
    chanals = db.get_available_chanals(message.from_user.id)
    if chanals:
        await message.answer(
            "Подпишитесь на каналы",
            reply_markup=kb.chanals_keyboard()
        )
    else:
        await message.answer("Нет каналов")
    

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)