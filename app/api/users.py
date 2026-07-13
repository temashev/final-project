from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.crud import create_user, get_user_by_email, add_token_to_blacklist, update_user_password
from app.db.database import get_db_session
from app.dependencies import oauth2_scheme, get_current_user
from app.schemas import UserRegister, UserResponse, UserLogin, UserPasswordChange
from app.services.security import verify_password, create_access_token

users_router = APIRouter(prefix='/users', tags=['Пользователи'])
auth_router = APIRouter(prefix='/auth', tags=['Аутентификация'])


@auth_router.post('/register/', response_model=UserResponse)
async def register_user(user: UserRegister, db: AsyncSession = Depends(get_db_session)):
    # Отлавливание зарегистрированного имейла
    existing_user = await get_user_by_email(db=db, email=user.email)

    if existing_user:
        raise HTTPException(status_code=400, detail='Пользователь с таким email уже зарегистрирован')

    # Если имейла нет в БД, то регистрация
    new_user = await create_user(db=db, user_in=user)
    return new_user


@auth_router.post('/login/')
async def login_user(user: UserLogin, db: AsyncSession = Depends(get_db_session)):
    user_data = await get_user_by_email(db=db, email=user.email)
    if not user_data:
        raise HTTPException(status_code=401, detail='Неверный email или пароль')
    raw_password = user.password.get_secret_value()
    if not verify_password(raw_password, user_data.password):
        raise HTTPException(status_code=401, detail='Неверный email или пароль')

    token_payload = {
        'id': user_data.id,
        'email': user_data.email,
        'role': user_data.role
    }

    access_token = create_access_token(data=token_payload)

    return {'access_token': access_token, 'token_type': 'bearer'}


@auth_router.post('/logout/')
async def logout_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db_session)):
    await add_token_to_blacklist(db=db, token=token)

    return JSONResponse(content={"detail": "Вы успешно вышли из системы"})


@users_router.post('/change-password/')
async def change_password(
        password_data: UserPasswordChange,
        current_user = Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    raw_old_password = password_data.old_password.get_secret_value()
    if not verify_password(raw_old_password, current_user.password):
        raise HTTPException(status_code=401, detail='Неверный пароль')

    raw_new_password = password_data.new_password.get_secret_value()

    await update_user_password(user=current_user, new_password=raw_new_password, db=db)

    return {'message': 'Пароль обновлен успешно'}


@users_router.get('/me/', response_model=UserResponse)
async def get_my_profile(
        current_user = Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    return current_user
