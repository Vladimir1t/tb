#include <iostream>
#include <tg_bot.hpp>

/** @brief tg-bot for ranging queries
 *  @param token you can get it from BotFather
 */
int main() {

    my::tg_bot bot("write_here_token");  // токен бота 

    bot.run_bot();

    return 0;
}