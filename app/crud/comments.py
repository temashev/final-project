from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import models


async def create_comment(text: str, db: AsyncSession, team_id: int, task_id: int, user_id: int):
    new_comment = models.Comment(
        text=text,
        created_at=datetime.now(),
        user_id=user_id,
        team_id=team_id,
        task_id=task_id
    )

    db.add(new_comment)

    await db.commit()
    await db.refresh(new_comment)

    return new_comment


async def show_comments_list(task_id: int, team_id: int, db: AsyncSession):
    stmt = select(models.Comment).where(
        models.Comment.team_id == team_id,
        models.Comment.task_id == task_id
    ).options(selectinload(models.Comment.user))


    result = await db.execute(stmt)

    return result.scalars().all()
