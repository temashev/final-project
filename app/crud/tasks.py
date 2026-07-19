from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import schemas
from app.db import models


async def create_task(task_data: schemas.TaskCreate, db: AsyncSession, team_id: int, user_id: int):
    """
    Создание задачи
    """
    new_task = models.Task(
        title=task_data.title,
        description=task_data.description,
        due_date=task_data.due_date,
        user_id=user_id,
        team_id=team_id,
        status=task_data.status
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task


async def get_tasks_by_team(team_id: int, db: AsyncSession):
    """
    Получение всех задач команды
    """
    stmt = select(models.Task).where(models.Task.team_id == team_id)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_task_by_id(task_id: int, team_id: int, db: AsyncSession):
    """
    Получение задачи по айди
    """
    stmt = select(models.Task).where(
        models.Task.id == task_id, models.Task.team_id == team_id
    ).options(selectinload(models.Task.evaluation))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_task(task_id: int, team_id: int, update_data: dict, db: AsyncSession):
    """
    Обновление задачи
    """
    task = await get_task_by_id(task_id=task_id, team_id=team_id, db=db)
    if not task:
        return None

    for k, v in update_data.items():
        setattr(task, k, v)

    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(task_id: int, team_id: int, db: AsyncSession):
    """
    Удаление задачи
    """
    task = await get_task_by_id(task_id=task_id, team_id=team_id, db=db)
    if not task:
        return None

    await db.delete(task)
    await db.commit()
    return True
