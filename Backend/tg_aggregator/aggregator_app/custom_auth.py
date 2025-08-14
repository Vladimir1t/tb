# aggregator_app/custom_auth.py

import hmac
import hashlib
from urllib.parse import unquote

from rest_framework.permissions import BasePermission
from django.conf import settings

def validate_telegram_data(init_data: str):
    """
    Валидирует initData, полученные от Telegram WebApp.
    """
    try:
        # Сортируем и форматируем данные
        parsed_data = sorted([
            (key, value) for key, value in
            (pair.split('=') for pair in unquote(init_data).split('&'))
        ], key=lambda x: x[0])

        # Извлекаем хеш для проверки
        auth_hash = ""
        for key, value in parsed_data:
            if key == 'hash':
                auth_hash = value
                break
        
        # Формируем строку для проверки
        data_check_string = "\n".join([f"{key}={value}" for key, value in parsed_data if key != 'hash'])

        # Генерируем секретный ключ
        secret_key = hmac.new(
            "WebAppData".encode(),
            settings.TELEGRAM_BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()
        
        # Генерируем хеш из наших данных
        h = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256)
        
        # Сравниваем хеши
        return h.hexdigest() == auth_hash
    except Exception:
        return False

class IsTelegramAuthenticated(BasePermission):
    """
    Проверяет наличие и валидность заголовка X-Telegram-Init-Data.
    """
    def has_permission(self, request, view):
        init_data = request.headers.get('X-Telegram-Init-Data')
        if not init_data:
            return False
        return validate_telegram_data(init_data)