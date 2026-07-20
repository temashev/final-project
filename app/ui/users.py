from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from app.api.users import register_user, login_user, change_password, get_my_profile, update_profile
from app.db.database import get_db_session
from app.dependencies import get_current_user
from app.schemas import UserRegister, UserPasswordChange, UserProfileUpdate

ui_users_router = APIRouter(prefix='/ui', tags=['Фронтенд'])
templates = Jinja2Templates(directory='templates')


async def get_token_from_cookie(request: Request):
    # Хелпер для авторизации через Cookie
    token = request.cookies.get('access_token')
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return token.replace('Bearer ', '') if 'Bearer ' in token else token


async def get_current_user_from_cookie(
        token: str = Depends(get_token_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    return await get_current_user(token=token, db=db)


@ui_users_router.get('/register/', response_class=HTMLResponse)
async def render_register_page(request: Request):
    return templates.TemplateResponse(request=request, name='users/register.html')


@ui_users_router.post('/register/')
async def handle_register(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
        full_name: str = Form(...),
        db: AsyncSession = Depends(get_db_session)
):
    user_data = UserRegister(email=email, password=password, full_name=full_name)

    try:
        await register_user(user=user_data, db=db)

        return RedirectResponse(url='/ui/login/', status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}. <a href="/ui/register/">Назад</a>', status_code=e.status_code)


@ui_users_router.get('/login/', response_class=HTMLResponse)
async def render_login_page(request: Request):
    return templates.TemplateResponse(request=request, name='users/login.html')


@ui_users_router.post('/login/')
async def handle_login(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        db: AsyncSession = Depends(get_db_session)
):
    try:
        from fastapi.security import OAuth2PasswordRequestForm
        form_data = OAuth2PasswordRequestForm(username=username, password=password)

        token_data = await login_user(form_data=form_data, db=db)

        response = RedirectResponse(url='/ui/me/', status_code=status.HTTP_303_SEE_OTHER)

        response.set_cookie(
            key='access_token',
            value=f'Bearer {token_data["access_token"]}',
            httponly=True,
            max_age=1800
        )
        return response
    except HTTPException:
        return HTMLResponse(content='Неверный логин или пароль. <a href=\"/ui/login/\">Назад</a>', status_code=401)


@ui_users_router.get('/change-password/', response_class=HTMLResponse)
async def render_change_password_page(
        request: Request,
        current_user=Depends(get_current_user_from_cookie)
):
    return templates.TemplateResponse(request=request, name='users/change_password.html')


@ui_users_router.post('/change-password/')
async def handle_change_password(
        request: Request,
        old_password: str = Form(...),
        new_password: str = Form(...),
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    password_data = UserPasswordChange(old_password=old_password, new_password=new_password)

    try:
        await change_password(password_data=password_data, current_user=current_user, db=db)
        return RedirectResponse(url='/ui/me/', status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}. <a href="/ui/change-password/">Назад</a>',
                            status_code=e.status_code)


@ui_users_router.get('/me/', response_class=HTMLResponse)
async def render_profile(
        request: Request,
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    user_data = await get_my_profile(current_user=current_user, db=db)

    return templates.TemplateResponse(
        request=request,
        name='users/profile.html',
        context={'user': user_data}
    )


@ui_users_router.post('/logout/')
async def handle_logout(request: Request):
    response = RedirectResponse(url='/ui/login/', status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie('access_token')
    return response


@ui_users_router.post('/me/update/')
async def handle_update_profile(
        request: Request,
        full_name: str = Form(None),
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    update_data = UserProfileUpdate(full_name=full_name)

    try:
        await update_profile(updated_data=update_data, current_user=current_user, db=db)
        return RedirectResponse(url='/ui/me/', status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}. <a href="/ui/me/">Назад</a>', status_code=e.status_code)
