# aggregator_app/utils.py

import requests
from urllib.parse import urlparse
from typing import Optional

def get_telegram_avatar_url(link: str) -> Optional[str]:
    """Получает URL аватарки Telegram канала/бота по t.me ссылке."""
    try:
        parsed = urlparse(link)
        if not parsed.netloc.endswith('t.me'):
            return None
        
        username = parsed.path.strip('/')
        if not username:
            return None
        
        # Используем API t.me для получения аватара
        avatar_url = f"https://t.me/i/userpic/320/{username}.jpg"
        # Проверяем, что аватар действительно существует
        response = requests.head(avatar_url, timeout=3, allow_redirects=True)
        
        # Если ответ успешный и это изображение, возвращаем URL
        if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
            return avatar_url
        return None
    except requests.RequestException:
        return None