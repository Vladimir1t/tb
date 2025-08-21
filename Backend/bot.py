import telebot;
bot = telebot.TeleBot('8143528604:AAEiouPy36hamVNvQhJK3ptZsiaUXJjkwIs');

def bot_get_text_messages(message):
    """initial bot"""
    if message.text == "/start":
        bot.send_message(message.from_user.id, "Привет, Это Telegram Catalog. Скорее нажимай на кнопку и ищи нужные тебе каналы и ботов по категориям")
    elif message.text == "/help":
        bot.send_message(message.from_user.id, "Это приложение ищет каналы, ботов и мини приложения по категориям. Жми на кнопку 'Открыть'")
    else:
        bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши /help.")

def run_bot():
    bot.polling(none_stop=True)