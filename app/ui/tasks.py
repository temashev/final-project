from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from app.api.tasks import list_tasks, add_task, show_comments, task_update, task_delete, add_comment, add_evaluation
from app.crud.tasks import get_task_by_id
from app.db.database import get_db_session
from app.schemas import TaskCreate, TaskUpdate, CommentCreate, EvaluationCreate
from app.ui.users import get_current_user_from_cookie

ui_tasks_router = APIRouter(prefix='/ui/teams', tags=['Фронтенд Задач'])

templates = Jinja2Templates(directory='templates')


@ui_tasks_router.get('/{team_id}/tasks/', response_class=HTMLResponse)
async def render_tasks_list(
        request: Request,
        team_id: int,
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    try:
        tasks = await list_tasks(team_id=team_id, current_user=current_user, db=db)
        return templates.TemplateResponse(
            request=request,
            name='tasks/list.html',
            context={'team_id': team_id, 'tasks': tasks}
        )
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}', status_code=e.status_code)


@ui_tasks_router.post('/{team_id}/tasks/create/')
async def ui_add_task(
        team_id: int,
        title: str = Form(...),
        description: str = Form(...),
        due_date: date = Form(...),
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    task_data = TaskCreate(title=title, description=description, due_date=due_date)
    try:
        await add_task(task_data=task_data, team_id=team_id, current_user=current_user, db=db)
        return RedirectResponse(url=f'/ui/teams/{team_id}/tasks/', status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}', status_code=e.status_code)


@ui_tasks_router.get('/{team_id}/tasks/{task_id}/', response_class=HTMLResponse)
async def render_task_detail(
        request: Request,
        team_id: int,
        task_id: int,
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    try:
        task = await get_task_by_id(team_id=team_id, task_id=task_id, db=db)
        if not task:
            return HTMLResponse(content='Задача не найдена', status_code=404)

        comments = await show_comments(team_id=team_id, task_id=task_id, current_user=current_user, db=db)

        return templates.TemplateResponse(
            request=request,
            name='tasks/detail.html',
            context={'team_id': team_id, 'task': task, 'comments': comments}
        )
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}', status_code=e.status_code)


@ui_tasks_router.post('/{team_id}/tasks/{task_id}/update/')
async def ui_task_update(
        team_id: int,
        task_id: int,
        status_field: str = Form(..., alias='status'),  # Pydantic заберет status
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    update_data = TaskUpdate(status=status_field)
    try:
        await task_update(
            update_data=update_data, team_id=team_id, task_id=task_id,
            current_user=current_user, db=db
        )
        return RedirectResponse(url=f'/ui/teams/{team_id}/tasks/{task_id}/', status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}', status_code=e.status_code)


@ui_tasks_router.post('/{team_id}/tasks/{task_id}/delete/')
async def ui_task_delete(
        team_id: int,
        task_id: int,
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    try:
        await task_delete(team_id=team_id, task_id=task_id, current_user=current_user, db=db)
        return RedirectResponse(url=f'/ui/teams/{team_id}/tasks/', status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}', status_code=e.status_code)


@ui_tasks_router.post('/{team_id}/tasks/{task_id}/comments/create/')
async def ui_add_comment(
        team_id: int,
        task_id: int,
        text: str = Form(...),
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    comment_data = CommentCreate(text=text)
    try:
        await add_comment(
            comment_data=comment_data, team_id=team_id, task_id=task_id,
            current_user=current_user, db=db
        )
        return RedirectResponse(url=f'/ui/teams/{team_id}/tasks/{task_id}/', status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}', status_code=e.status_code)


@ui_tasks_router.post('/{team_id}/tasks/{task_id}/evaluation/')
async def ui_add_evaluation(
        team_id: int,
        task_id: int,
        score: int = Form(...),
        comment: str = Form(...),
        current_user=Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_db_session)
):
    eval_data = EvaluationCreate(score=score, comment=comment)
    try:
        await add_evaluation(
            eval_data=eval_data, team_id=team_id, task_id=task_id,
            current_user=current_user, db=db
        )
        return RedirectResponse(url=f'/ui/teams/{team_id}/tasks/{task_id}/', status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return HTMLResponse(content=f'Ошибка: {e.detail}', status_code=e.status_code)
