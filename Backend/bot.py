import telebot

API_TOKEN = "8143528604:AAEiouPy36hamVNvQhJK3ptZsiaUXJjkwIs"
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(content_types=['text'])
def bot_get_text_messages(message):
    if message.text == "/start":
        bot.send_message(
            message.from_user.id,
            "Привет! Это Telegram Catalog. Жми кнопку и ищи каналы/ботов по категориям."
        )
    elif message.text == "/help":
        bot.send_message(
            message.from_user.id,
            "Это приложение ищет каналы, ботов и мини-приложения по категориям."
        )
    else:
        bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши /help.")

def run_bot():
    bot.polling(none_stop=True)
