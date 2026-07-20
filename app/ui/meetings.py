from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from app.api.meetings import list_meetings, add_meeting, meeting_update, meeting_delete, calendar
from app.db.database import get_db_session
from app.schemas import MeetingCreate, MeetingUpdate
from app.ui.users import get_current_user_from_cookie

ui_meetings_router = APIRouter(prefix='/ui/teams', tags=['Фронтенд Встреч'])

templates = Jinja2Templates(directory="templates")


@ui_meetings_router.get('/{team_id}/meetings/', response_class=HTMLResponse)
async def render_meetings_list(
        request: Request,
        team_id: int,
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    try:
        meetings = await list_meetings(team_id=team_id, current_user=current_user, db=db)
        return templates.TemplateResponse(
            request=request, name='meetings/list.html',
            context={'team_id': team_id, 'meetings': meetings}
        )
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}', status_code=e.status_code)


@ui_meetings_router.post('/{team_id}/meetings/create/')
async def ui_create_meeting(
        team_id: int,
        starts_at: datetime = Form(...),
        ends_at: datetime = Form(...),
        member_ids_str: str = Form('', alias='member_ids'),
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    members = []
    if member_ids_str.strip():
        try:
            members = [int(m.strip()) for m in member_ids_str.split(',') if m.strip().isdigit()]
        except ValueError:
            return HTMLResponse(content='Ошибка: ID участников должны быть числами', status_code=400)

    meeting_data = MeetingCreate(starts_at=starts_at, ends_at=ends_at, member_ids=members)

    try:
        await add_meeting(meeting_data=meeting_data, team_id=team_id, current_user=current_user, db=db)
        return RedirectResponse(url=f'/ui/teams/{team_id}/meetings/', status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}', status_code=e.status_code)


@ui_meetings_router.post('/{team_id}/meetings/{meeting_id}/update/')
async def ui_update_meeting(
        team_id: int,
        meeting_id: int,
        starts_at: datetime = Form(None),
        ends_at: datetime = Form(None),
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    update_data = MeetingUpdate(starts_at=starts_at, ends_at=ends_at)
    try:
        await meeting_update(updated_data=update_data, team_id=team_id, meeting_id=meeting_id,
                             current_user=current_user, db=db)
        return RedirectResponse(url=f'/ui/teams/{team_id}/meetings/{meeting_id}/',
                                status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}', status_code=e.status_code)


@ui_meetings_router.post('/{team_id}/meetings/{meeting_id}/delete/')
async def ui_delete_meeting(
        team_id: int,
        meeting_id: int,
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    try:
        await meeting_delete(team_id=team_id, meeting_id=meeting_id, current_user=current_user, db=db)
        return RedirectResponse(url=f'/ui/teams/{team_id}/meetings/', status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}', status_code=e.status_code)


@ui_meetings_router.get('/ui/calendar/', response_class=HTMLResponse)
async def render_calendar(
        request: Request,
        from_date: date = Query(None, alias='from_date'),
        to_date: date = Query(None, alias='to_date'),
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    if not from_date or not to_date:
        from_date = date.today()
        to_date = from_date + timedelta(days=7)

    try:
        meetings = await calendar(from_date=from_date, to_date=to_date, current_user=current_user, db=db)
        return templates.TemplateResponse(
            request=request, name='meetings/calendar.html',
            context={
                'meetings': meetings,
                'current_from': from_date.isoformat(),
                'current_to': to_date.isoformat()
            }
        )
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}', status_code=e.status_code)
