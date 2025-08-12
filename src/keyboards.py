from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Главная страница")],
            [KeyboardButton(text="Мой проект"), KeyboardButton(text="Банер AdGram")],
            [KeyboardButton(text="Личный профиль")]
        ],
        resize_keyboard=True
    )

def content_type_menu():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Каналы", callback_data="channels"),
        InlineKeyboardButton("Боты", callback_data="bots"),
        InlineKeyboardButton("Мини-приложения", callback_data="mini_apps")
    )
    return markup

def project_type_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Канал")],
            [KeyboardButton(text="Бот")],
            [KeyboardButton(text="Мини-приложение")],
            [KeyboardButton(text="Назад")]
        ],
        resize_keyboard=True
    )

def payment_method_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Бесплатно (за выполнение условий)")],
            [KeyboardButton(text="Платно")],
            [KeyboardButton(text="Назад")]
        ],
        resize_keyboard=True
    )

def tasks_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Разместить банер (+5🌟)", callback_data="task_banner"))
    markup.add(InlineKeyboardButton("Подписаться на канал (+3🌟)", callback_data="task_subscribe"))
    markup.add(InlineKeyboardButton("Пригласить друга (+10🌟)", callback_data="task_invite"))
    return markup

def profile_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пополнить баланс", callback_data="task_balance")],
            [KeyboardButton(text="Мои проекты", callback_data="task_projects")],
            [KeyboardButton(text="Назад", callback_data="task_back")]
        ],
        resize_keyboard=True
    )

def chanals_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("https://t.me/+O2g2YKynlB1jNGEy", callback_data="chanal"))
    return markup
