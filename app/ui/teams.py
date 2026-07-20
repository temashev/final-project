from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from app.api.teams import register_team, join_team, get_team_members, change_members_role, delete_team_member, \
    leave_from_team
from app.db.database import get_db_session
from app.schemas import TeamCreate, UpdateRoleRequest
from app.ui.users import get_current_user_from_cookie

ui_teams_router = APIRouter(prefix="/ui/teams", tags=["Фронтенд Команд"])
templates = Jinja2Templates(directory="templates")


@ui_teams_router.get('/', response_class=HTMLResponse)
async def render_teams_dashboard(
        request: Request,
        current_user=Depends(get_current_user_from_cookie)
):
    return templates.TemplateResponse(request=request, name='teams/dashboard.html')


@ui_teams_router.post('/create/')
async def ui_create_team(
        request: Request,
        name: str = Form(...),
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    team_data = TeamCreate(name=name)
    try:
        new_team = await register_team(new_team=team_data, db=db, current_user=current_user)
        return RedirectResponse(url=f'/ui/teams/{new_team.id}/', status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}. <a href="/ui/teams/">Назад</a>', status_code=e.status_code)


@ui_teams_router.post('/join/')
async def ui_join_team(
        request: Request,
        invite_code: str = Form(...),
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    try:
        await join_team(invite_code=invite_code, db=db, current_user=current_user)
        return RedirectResponse(url='/ui/teams/', status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}. <a href="/ui/teams/">Назад</a>', status_code=e.status_code)


@ui_teams_router.get('/{team_id}/', response_class=HTMLResponse)
async def render_team_detail(
        request: Request,
        team_id: int,
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    try:
        team = await get_team_members(team_id=team_id, current_user=current_user, db=db)
        return templates.TemplateResponse(
            request=request,
            name='teams/detail.html',
            context={'team': team}
        )
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}. <a href="/ui/teams/">Назад</a>', status_code=e.status_code)


@ui_teams_router.post('/{team_id}/members/{user_id}/role/')
async def ui_change_role(
        team_id: int,
        user_id: int,
        new_role: str = Form(...),
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    role_data = UpdateRoleRequest(role=new_role)
    try:
        await change_members_role(
            new_role=role_data, team_id=team_id, user_id=user_id,
            current_user=current_user, db=db
        )
        return RedirectResponse(url=f'/ui/teams/{team_id}/', status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}. <a href="/ui/teams/{team_id}/">Назад</a>',
                            status_code=e.status_code)


@ui_teams_router.post('/{team_id}/members/{user_id}/delete/')
async def ui_delete_member(
        team_id: int,
        user_id: int,
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    try:
        await delete_team_member(team_id=team_id, user_id=user_id, current_user=current_user, db=db)
        return RedirectResponse(url=f'/ui/teams/{team_id}/', status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}. <a href="/ui/teams/{team_id}/">Назад</a>',
                            status_code=e.status_code)


@ui_teams_router.post('/{team_id}/leave/')
async def ui_leave_team(
        team_id: int,
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    try:
        await leave_from_team(team_id=team_id, current_user=current_user, db=db)
        return RedirectResponse(url='/ui/teams/', status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}. <a href="/ui/teams/{team_id}/">Назад</a>',
                            status_code=e.status_code)
