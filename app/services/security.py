import jwt

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from passlib.context import CryptContext

from app.config.settings import settings

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_password_hash(password: str) -> str:
    '''
    Принимает пароль и возвращает его хэш
    '''
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    '''
    Сравнивает пароль с хэшем из БД
    '''
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    '''
    Добавляет время создания и истечения токена
    '''
    payload = data.copy()
    payload.update({
        'exp': datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        'iat': datetime.now(timezone.utc)
    })

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    '''
    Проверяет валидность токена
    '''
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Время действия токена истекло')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Невалидный токен')
