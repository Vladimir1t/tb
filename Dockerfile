# Ubuntu
FROM ubuntu:latest

#  зависимости
RUN apt update && apt install -y \
    g++ cmake make \
    libboost-all-dev libssl-dev libcurl4-openssl-dev \
    git

# tgbot-cpp
RUN git clone https://github.com/reo7sp/tgbot-cpp.git /tgbot-cpp \
    && cd /tgbot-cpp && mkdir build && cd build \
    && cmake .. && make -j$(nproc) && make install

# директория 
WORKDIR /app
COPY . /app

# Собирка
RUN rm -rf build && mkdir build && cd build && cmake -DCMAKE_BUILD_TYPE=Release -S /app -B /app/build \
    && cmake --build /app/build

# Запуск
CMD ["/app/build/tg_bot.x"]


# docker build -t telegram-bot .  -- сборка образа 
# docker run -d --name telegram-bot telegram-bot   -- создание контейнера и запуск бота
# docker logs telegram-bot  -- логи

# docker rm telegram-bot   -- удаление контейнера 
# docker stop telegram-bot

# docker stats telegram-bot
# docker inspect telegram-bot

# Docker позволяет создавать изолированные среды для приложений, 
# которые работают одинаково на всех системах. Он предоставляет простоту переноса, 
# управление зависимостями, масштабируемость, упрощает развертывание и управление 
# многоконтейнерными приложениями.

