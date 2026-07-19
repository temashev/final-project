from fastapi import Depends, APIRouter, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.crud.users import get_user_by_email
from app.db.database import get_db_session
from app.dependencies import oauth2_scheme, get_current_user
from app.schemas import UserRegister, UserProfileResponse, UserPasswordChange, UserProfileUpdate, \
    UserRegisterResponse
from app.core.security import verify_password, create_access_token
from app.services.users import update_user_password, get_user_profile_data, update_user_profile, add_token_to_blacklist, \
    create_user

users_router = APIRouter(prefix='/users', tags=['Пользователи'])
auth_router = APIRouter(prefix='/auth', tags=['Аутентификация'])


@auth_router.post('/register/', response_model=UserRegisterResponse)
async def register_user(user: UserRegister, db: AsyncSession = Depends(get_db_session)):
    # Отлавливание зарегистрированного имейла
    existing_user = await get_user_by_email(db=db, email=user.email)

    if existing_user:
        raise HTTPException(status_code=400, detail='Пользователь с таким email уже зарегистрирован')

    # Если имейла нет в БД, то регистрация
    new_user = await create_user(db=db, user_in=user)
    return new_user


@auth_router.post('/login/')
async def login_user(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db_session)
):
    user_data = await get_user_by_email(db=db, email=form_data.username)
    if not user_data:
        raise HTTPException(status_code=401, detail='Неверный email или пароль')
    raw_password = form_data.password
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
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    raw_old_password = password_data.old_password.get_secret_value()
    if not verify_password(raw_old_password, current_user.password):
        raise HTTPException(status_code=401, detail='Неверный пароль')

    raw_new_password = password_data.new_password.get_secret_value()

    await update_user_password(user=current_user, new_password=raw_new_password, db=db)

    return {'message': 'Пароль обновлен успешно'}


@users_router.get('/me/', response_model=UserProfileResponse)
async def get_my_profile(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    user = await get_user_profile_data(user_id=current_user.id, db=db)
    return user


@users_router.patch('/update-profile')
async def update_profile(
        updated_data: UserProfileUpdate,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session),

):
    update_dict = updated_data.model_dump(exclude_unset=True)

    updated_user = await update_user_profile(user=current_user, updated_data=update_dict, db=db)

    if not updated_user:
        raise HTTPException(
            status_code=404,
            detail='Пользователь не найден или у вас недостаточно прав'
        )

    return updated_user
