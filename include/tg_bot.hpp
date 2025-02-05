#ifndef TG_BOT_HPP
#define TG_BOT_HPP

#include <iostream>
#include <string>
#include <tgbot/tgbot.h>

#include <red_black_tree.hpp>

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
            bot.getApi().sendMessage(message->chat->id, "Привет! Я Telegram бот (название) \nВозможные команды:" 
                            "/start /help /Hi /range_queries");
        });
        bot.getEvents().onCommand("Hi", [&bot](TgBot::Message::Ptr message) {
            bot.getApi().sendMessage(message->chat->id, "Привет!");
        });
        bot.getEvents().onCommand("help", [&bot](TgBot::Message::Ptr message) {
            bot.getApi().sendMessage(message->chat->id, "Возможные команды: /start /help /Hi /range_queries");
        });
        
        bot.getEvents().onCommand("range_queries", [&bot](TgBot::Message::Ptr message) {

            bot.getApi().sendMessage(message->chat->id, "Range queries. \nВведите режим: \nq  [для поиска количества элементов" 
                                "в диапазоне] \nk  [для добавления элемента]");
            bot.getEvents().onNonCommandMessage([&bot](TgBot::Message::Ptr message) {
                static int64_t key = 0;
                static char mode = '\0';
                static int64_t left = 0, right = 0;
                static bool waiting_for_left = false;
                static bool waiting_for_right = false;
                static Range_queries::range_quries<int64_t> range_quer;

                if (message->text.empty()) return;

                if (mode == '\0') {  
                    char new_mode = message->text[0];
                    if (new_mode == 'k' || new_mode == 'q') {
                        mode = new_mode;
                        bot.getApi().sendMessage(message->chat->id, "Режим установлен: " + std::string(1, mode));

                        if (mode == 'k') {
                            bot.getApi().sendMessage(message->chat->id, "Введите число для добавления:");
                        } 
                        else if (mode == 'q') {
                            bot.getApi().sendMessage(message->chat->id, "Введите два числа отдельно (левая и правая граница):");
                            waiting_for_left = true;
                        }
                    } 
                    else 
                        bot.getApi().sendMessage(message->chat->id, "Неверный режим. Введите 'k' или 'q'.");
                } 
                else if (mode == 'k') {  
                    try {
                        key = std::stoll(message->text);
                        range_quer.add_element(Range_queries::Mode::bot, key);
                        bot.getApi().sendMessage(message->chat->id, "Число добавлено: " + std::to_string(key));
                        mode = '\0';
                    } 
                    catch (const std::exception&) {
                        bot.getApi().sendMessage(message->chat->id, "Ошибка! Введите число.");
                    }
                } 
                else if (mode == 'q') {  
                    try {
                        if (waiting_for_left) {
                            left = std::stoll(message->text);
                            waiting_for_left = false;
                            waiting_for_right = true;
                            bot.getApi().sendMessage(message->chat->id, "Введите второе число (правая граница):");
                        } 
                        else if (waiting_for_right) {
                            right = std::stoll(message->text);
                            waiting_for_right = false;
                            bot.getApi().sendMessage(message->chat->id, "Диапазон: [" + std::to_string(left) + 
                                                    ", " + std::to_string(right) + "]");
                            bot.getApi().sendMessage(message->chat->id, 
                                "Результат: " + std::to_string(range_quer.find_range_elements(Range_queries::Mode::bot, left, right)));

                            mode = '\0'; 
                        }
                    } 
                    catch (const std::exception&) {
                        bot.getApi().sendMessage(message->chat->id, "Ошибка! Введите корректное число.");
                    }
                }
            });
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