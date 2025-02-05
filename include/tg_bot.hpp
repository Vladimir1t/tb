#ifndef TG_BOT_HPP
#define TG_BOT_HPP

#include <iostream>
#include <string>
#include <tgbot/tgbot.h>

namespace my {

class tg_bot {

protected:
    std::string token_;

public:

    tg_bot(std::string token) {
        token_ = token;
    }

private:

    void give_istructions(TgBot::Bot& bot) const {

        bot.getEvents().onCommand("start", [&bot](TgBot::Message::Ptr message) {
            bot.getApi().sendMessage(message->chat->id, "Привет, сладкий! Я Telegram бот vvv_bot (не мог лучше название придумать?)");
        });
        bot.getEvents().onCommand("Hi", [&bot](TgBot::Message::Ptr message) {
            bot.getApi().sendMessage(message->chat->id, "Привет!");
        });
        bot.getEvents().onCommand("help", [&bot](TgBot::Message::Ptr message) {
            bot.getApi().sendMessage(message->chat->id, "Себе помоги :)");
        });
        bot.getEvents().onAnyMessage([&bot](TgBot::Message::Ptr message) {
            if (StringTools::startsWith(message->text, "/start") || StringTools::startsWith(message->text, "/help"))
                return;
            std::string reply = "ничего не могу: " + message->text;
            bot.getApi().sendMessage(message->chat->id, reply);
            std::cout << message->text << std::endl;
        });
    } 

public:

    void run_bot() const {

        TgBot::Bot bot(token_);

        give_istructions(bot);

        try {
            std::cout << "Бот запущен..." << std::endl;
            TgBot::TgLongPoll longPoll(bot);
            while (true) {
                longPoll.start();
            }
        } 
        catch (TgBot::TgException &e) {
            std::cerr << "Ошибка: " << e.what() << std::endl;
        }
    }
};
}


#endif // TG_BOT_HPP