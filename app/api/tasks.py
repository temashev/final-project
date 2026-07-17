from fastapi import Depends, HTTPException, APIRouter, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import create_task, get_tasks_by_team, update_task, delete_task, check_user_in_team, create_comment, \
    show_comments_list
from app.db.database import get_db_session
from app.dependencies import get_current_user
from app.schemas import TaskCreate, TaskUpdate, CommentCreate, CommentResponse

task_router = APIRouter(prefix='/teams', tags=['Задачи'])


@task_router.post('/{team_id}/tasks/')
async def add_task(
        task_data: TaskCreate,
        team_id: int = Path(le=2147483647, ge=1),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    member = await check_user_in_team(team_id=team_id, user_id=current_user.id, db=db)

    if not member:
        raise HTTPException(status_code=403, detail='У вас нет доступа к задачам команды')

    new_task = await create_task(db=db, task_data=task_data, team_id=team_id)
    return new_task


@task_router.get('/{team_id}/tasks/')
async def list_tasks(
        team_id: int = Path(le=2147483647, ge=1),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    member = await check_user_in_team(team_id=team_id, user_id=current_user.id, db=db)

    if not member:
        raise HTTPException(status_code=403, detail='У вас нет доступа к задачам команды')

    tasks = await get_tasks_by_team(team_id=team_id, db=db)
    return tasks


@task_router.patch('/{team_id}/tasks/{task_id}')
async def task_update(
        update_data: TaskUpdate,
        team_id: int = Path(le=2147483647, ge=1),
        task_id: int = Path(le=2147483647, ge=1),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    member = await check_user_in_team(team_id=team_id, user_id=current_user.id, db=db)

    if not member:
        raise HTTPException(status_code=403, detail='У вас нет доступа к задачам команды')

    # Перевод в словарь, т.к. в update_task перебор по словарю
    update_dict = update_data.model_dump(exclude_unset=True)

    updated_task = await update_task(task_id=task_id, team_id=team_id, update_data=update_dict, db=db)

    if not updated_task:
        raise HTTPException(
            status_code=404,
            detail='Задача не найдена, ее нет в списке или у вас недостаточно прав'
        )

    return updated_task


@task_router.delete('/{team_id}/tasks/{task_id}')
async def task_delete(
        team_id: int = Path(le=2147483647, ge=1),
        task_id: int = Path(le=2147483647, ge=1),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    member = await check_user_in_team(team_id=team_id, user_id=current_user.id, db=db)

    if not member:
        raise HTTPException(status_code=403, detail='У вас нет доступа к задачам команды')

    task = await delete_task(task_id=task_id, team_id=team_id, db=db)
    if not task:
        raise HTTPException(status_code=404, detail=f'Задачи с id:{task_id} не существует')
    return {'detail': 'Задача успешно удалена'}


@task_router.post('/{team_id}/tasks/{task_id}/comments')
async def add_comment(
        comment_data: CommentCreate,
        team_id: int = Path(le=2147483647, ge=1),
        task_id: int = Path(le=2147483647, ge=1),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    member = await check_user_in_team(team_id=team_id, user_id=current_user.id, db=db)

    if not member:
        raise HTTPException(status_code=403, detail='У вас нет доступа к задачам команды')

    new_comment = await create_comment(
        db=db,
        team_id=team_id,
        user_id=member.user_id,
        task_id=task_id,
        comment_data=comment_data
    )
    return new_comment


@task_router.get('/{team_id}/tasks/{task_id}/comments', response_model=list[CommentResponse])
async def show_comments(
        team_id: int = Path(le=2147483647, ge=1),
        task_id: int = Path(le=2147483647, ge=1),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    member = await check_user_in_team(team_id=team_id, user_id=current_user.id, db=db)

    if not member:
        raise HTTPException(status_code=403, detail='У вас нет доступа к задачам команды')

    comments = await show_comments_list(team_id=team_id, task_id=task_id, db=db)
    return comments
