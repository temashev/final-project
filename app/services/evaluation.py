from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.crud.evaluation import update_evaluation, create_evaluation
from app.crud.tasks import get_task_by_id


async def add_evaluation(task_id: int, team_id: int, eval_data: schemas.EvaluationCreate, db: AsyncSession):
    task = await get_task_by_id(
        task_id=task_id,
        team_id=team_id,
        db=db
    )

    if not task:
        return None

    if task.evaluation:
        return await update_evaluation(
            evaluation=task.evaluation,
            score=eval_data.score,
            comment=eval_data.comment,
            db=db
        )

    return await create_evaluation(
        score=eval_data.score,
        comment=eval_data.comment,
        task_id=task_id,
        db=db
    )
