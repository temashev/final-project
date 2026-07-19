from fastapi import Depends, HTTPException, APIRouter, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.comments import show_comments_list
from app.services.comments import add_comment as service_create_comment
from app.services.evaluation import add_evaluation as service_add_evaluation
from app.crud.tasks import create_task, get_tasks_by_team, update_task, delete_task, get_task_by_id
from app.crud.teams import check_user_in_team
from app.db.database import get_db_session
from app.dependencies import get_current_user
from app.schemas import TaskCreate, TaskUpdate, CommentCreate, CommentResponse, EvaluationCreate
from app.services.teams import check_is_user_team_manager

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

    new_task = await create_task(db=db, task_data=task_data, team_id=team_id, user_id=current_user.id)
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
    task = await get_task_by_id(team_id=team_id, task_id=task_id, db=db)
    if not task:
        raise HTTPException(status_code=404, detail='Задача не найдена')

    is_manager = await check_is_user_team_manager(team_id=team_id, user_id=current_user.id, db=db)
    is_creator = task.user_id == current_user.id

    if not (is_manager or is_creator):
        raise HTTPException(status_code=403, detail='Обновлять задачу может только создатель или менеджер')

    # Перевод в словарь, т.к. в update_task перебор по словарю
    update_dict = update_data.model_dump(exclude_unset=True)
    updated_task = await update_task(task_id=task_id, team_id=team_id, update_data=update_dict, db=db)

    return updated_task


@task_router.delete('/{team_id}/tasks/{task_id}')
async def task_delete(
        team_id: int = Path(le=2147483647, ge=1),
        task_id: int = Path(le=2147483647, ge=1),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    task = await get_task_by_id(team_id=team_id, task_id=task_id, db=db)
    if not task:
        raise HTTPException(status_code=404, detail=f'Задачи с id:{task_id} не существует')

    is_manager = await check_is_user_team_manager(team_id=team_id, user_id=current_user.id, db=db)
    is_creator = task.user_id == current_user.id

    if not (is_manager or is_creator):
        raise HTTPException(status_code=403, detail='Удалять задачу может только ее создатель или менеджер команды')

    await delete_task(task_id=task_id, team_id=team_id, db=db)
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

    new_comment = await service_create_comment(
        db=db,
        team_id=team_id,
        user_id=current_user.id,
        task_id=task_id,
        comment_data=comment_data
    )

    if not new_comment:
        raise HTTPException(status_code=404, detail='Задача не найдена')

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


@task_router.post('/{team_id}/tasks/{task_id}/evaluation')
async def add_evaluation(
        eval_data: EvaluationCreate,
        team_id: int = Path(le=2147483647, ge=1),
        task_id: int = Path(le=2147483647, ge=1),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    manager = await check_is_user_team_manager(team_id=team_id, user_id=current_user.id, db=db)
    if not manager:
        raise HTTPException(status_code=403, detail='У вас нет доступа к задачам команды')

    task = await get_task_by_id(team_id=team_id, task_id=task_id, db=db)
    if not task:
        raise HTTPException(status_code=404, detail='Задача не найдена')
    if task.status != 'done':
        raise HTTPException(status_code=403, detail='Задача еще не закрыта')

    new_evaluation = await service_add_evaluation(
        task_id=task_id,
        team_id=team_id,
        eval_data=eval_data,
        db=db
    )
    return new_evaluation
