# Telegram Aggregator - README

## Описание проекта

Telegram Aggregator - это веб-приложение для поиска и каталогизации Telegram-каналов, ботов и мини-приложений. 

Пользователи могут:

- Просматривать каталог проектов, отсортированных по категориям
- Видеть премиум-каналы и боты
- Отслеживать количество подписчиков и лайков
- Управлять своим профилем

## Технологии

### Бэкенд
- **Python** с **FastAPI** (основной фреймворк)
- **SQLite** (база данных)
- **Uvicorn** (ASGI-сервер)
- **Render** (хостинг)

### Фронтенд
- **HTML/CSS/JavaScript**
- **Telegram WebApp API** для интеграции с Telegram
- **Vercel** (хостинг фронтенда)

## Установка и запуск

### Локальная разработка

1.
```bash
git clone https://github.com/Vladimir1t/Telegram-bot.git
```

2. Установите зависимости
```bash
pip install -r requirements.txt
```

3. Инициализируйте базу данных
```bash
python main.py
```

4. Запустите сервер
```bash
uvicorn main:app --reload
```

Фронтенд будет доступен по адресу: `https://telegram-bot-chi-lyart.vercel.app`

### Развертывание

1. **Бэкенд**:
   - Развертывается на Render.com как Python-сервис
   - Требуется файл `requirements.txt` с зависимостями

2. **Фронтенд**:
   - Развертывается на Vercel как статический сайт
   - Требуется указать переменную окружения `API_URL` с адресом бэкенда

## API Endpoints

### Основные endpoints:
- `GET /projects/` - Получить список проектов
  - Параметры:
    - `type` (channel/bot/mini_app)
    - `theme` (фильтрация по тематике)

- `POST /projects/` - Добавить новый проект
- `GET /users/{user_id}` - Получить данные пользователя
- `POST /users/{user_id}/complete_task` - Завершить задание

### Отладочные endpoints:
- `GET /ping` - Проверка работоспособности
- `GET /debug/db` - Информация о состоянии БД
- `GET /debug/projects` - Список всех проектов в БД

## Структура базы данных

### Таблицы:
1. **projects**:
   - id, type, name, link, theme, is_premium, likes, subscribers, user_id

2. **users**:
   - id, username, stars, balance

3. **tasks**:
   - user_id, task_type, completed

## Настройка окружения

Создайте файл `.env` в корне проекта:
```
API_URL=https://your-backend-url.onrender.com
```

## Лицензия

Запрещено копирование и использование в любых целях.

## Контакты

По вопросам сотрудничества и поддержки:
- Email: vekhov.vv@phystech.edu
- Telegram: @vladimir_v_spb