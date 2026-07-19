from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.crud.comments import create_comment, show_comments_list
from app.crud.tasks import get_task_by_id


async def add_comment(comment_data: schemas.CommentCreate, db: AsyncSession, team_id: int, task_id: int, user_id: int):
    task = await get_task_by_id(task_id=task_id, team_id=team_id, db=db)

    if not task:
        return None

    new_comment = await create_comment(text=comment_data.text, db=db, team_id=team_id, task_id=task_id, user_id=user_id)

    return new_comment


async def get_task_comments(
        task_id: int,
        team_id: int,
        db: AsyncSession
):
    comments = await show_comments_list(task_id=task_id, team_id=team_id, db=db)

    return [schemas.CommentResponse(
        id=comment.id,
        text=comment.text,
        created_at=comment.created_at,
        username=comment.user.full_name
    ) for comment in comments]
