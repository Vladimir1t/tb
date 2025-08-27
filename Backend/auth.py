# auth.py
import hmac
import hashlib
from fastapi import HTTPException, Request

def validate_telegram_data(token: str, init_data: str):
    try:
        secret = hmac.new(
            key=hashlib.sha256(token.encode()).digest(),
            msg=init_data.encode(),
            digestmod=hashlib.sha256
        )
        return secret.hexdigest()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def verify_telegram_auth(request: Request):
    """
    Зависимость (Dependency) для проверки наличия заголовка аутентификации Telegram.
    """
    if not request.headers.get('X-Telegram-Init-Data'):
        raise HTTPException(status_code=401, detail="Auth required")