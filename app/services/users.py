from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import schemas
from app.core.security import get_password_hash, decode_token
from app.crud import users
from app.db import models


async def create_user(db: AsyncSession, user_in: schemas.UserRegister):
    raw_password = user_in.password.get_secret_value()
    hashed_password = get_password_hash(raw_password)

    db_user = models.User(
        email=user_in.email,
        full_name=user_in.full_name,
        password=hashed_password,
        role='member'
    )

    return await users.create_user(db=db, db_user=db_user)


async def add_token_to_blacklist(db: AsyncSession, token: str):
    payload = decode_token(token)
    exp_date = datetime.fromtimestamp(payload.get('exp'))

    blacklist_token = models.BlackListTokens(token=token, expire_at=exp_date)

    return await users.add_token_to_blacklist(db=db, token=blacklist_token)


async def update_user_password(user: models.User, new_password: str, db: AsyncSession):
    hashed_password = get_password_hash(new_password)

    user.password = hashed_password

    await users.update_user(user=user, db=db)


async def update_user_profile(user: models.User, updated_data: dict, db: AsyncSession):
    """
    Обновление профиля юзера
    """
    if not user:
        return None

    for k, v in updated_data.items():
        setattr(user, k, v)

    return await users.update_user(user=user, db=db)


async def get_user_profile_data(user_id: int, db: AsyncSession):
    stmt = select(models.User).where(models.User.id == user_id).options(
        selectinload(models.User.tasks).selectinload(models.Task.evaluation)
    )

    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return None

    evaluations = []

    for task in user.tasks:
        if task.evaluation is not None:
            evaluations.append(task.evaluation)

    avg_eval = 0.0

    if len(evaluations) > 0:
        scores = sum(eval.score for eval in evaluations)
        avg_eval = scores / len(evaluations)

    return {
        'id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'role': user.role,
        'avg_score': avg_eval,
        'evaluations': evaluations
    }
