cmake_minimum_required(VERSION 3.11)
project("Telegram_bot")

set(CMAKE_CXX_STANDARD 17)
include_directories(/usr/local/include /opt/homebrew/include)
link_directories(/usr/local/lib /opt/homebrew/lib)
include_directories(/usr/local/include/tgbot)
find_package(TgBot REQUIRED)
find_package(Boost REQUIRED COMPONENTS system)

# set(test_srcs
#     tests/src/tests.cpp
# )

set(srcs
    src/tg_bot.cpp
)
set(CMAKE_CXX_FLAGS_RELEASE "-O2")
set(FLAGS_DEBUG_1   "-g")
set(FLAGS_DEBUG_2   "-D NDEBUG")

add_library(tg_bot_lib STATIC ${srcs})
target_include_directories(tg_bot_lib PUBLIC "include")

add_executable(tg_bot.x src/tg_bot.cpp)
target_link_libraries(tg_bot.x tg_bot_lib)
target_link_libraries(tg_bot.x TgBot::TgBot)

# add_library(test_lib STATIC ${test_srcs})
# target_include_directories(test_lib PUBLIC "include")

# add_executable(test.x ${test_srcs})
# target_link_libraries(test.x test_lib)

# target_compile_options(test.x PRIVATE "$<$<CONFIG:RELEASE>:${CMAKE_CXX_FLAGS_RELEASE}>" ${FLAGS_DEBUG_1} ${FLAGS_DEBUG_2})
target_compile_options(tg_bot.x PRIVATE "$<$<CONFIG:RELEASE>:${CMAKE_CXX_FLAGS_RELEASE}>" ${FLAGS_DEBUG_1} ${FLAGS_DEBUG_2})

# cmake -DCMAKE_BUILD_TYPE=Release -S . -B build
# cmake --build build
# ./build/intersection.x
#
# cmake .. -DCMAKE_CXX_INCLUDE_WHAT_YOU_USE=./../../../../include-what-you-use/build/bin/include-what-you-use
# make
