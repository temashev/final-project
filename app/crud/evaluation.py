from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models


async def create_evaluation(score: int, comment: str, task_id: int, db: AsyncSession):
    evaluation = models.Evaluation(
        score=score,
        comment=comment,
        task_id=task_id
    )

    db.add(evaluation)

    await db.commit()
    await db.refresh(evaluation)

    return evaluation


async def update_evaluation(evaluation: models.Evaluation, score: int, comment: str, db: AsyncSession):
    evaluation.score = score
    evaluation.comment = comment

    await db.commit()
    await db.refresh(evaluation)

    return evaluation
