from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.crud import get_user_by_email, get_blacklisted_token
from app.db.database import get_db_session
from app.services.security import decode_token
from app.db import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login/')


async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Не удалось подтвердить учетные данные',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    payload = decode_token(token)
    email = payload.get('email')

    # Если имейла нет - ошибка
    if email is None:
        raise credentials_exception

    user = await get_user_by_email(db=db, email=email)

    # Если юзера нет в бд - ошибка
    if user is None:
        raise credentials_exception

    checked_token = await get_blacklisted_token(token=token, db=db)

    # Если токен в черном списке (отозван) - ошибка
    if checked_token is not None:
        raise credentials_exception

    return user


async def get_current_manager(current_user: models.User = Depends(get_current_user)):
    '''
    Проверяет юзера на наличие прав менеджера для создания команд
    '''
    if current_user.role != 'manager':
        raise HTTPException(status_code=403, detail='У вас недостаточно прав')
    return current_user
