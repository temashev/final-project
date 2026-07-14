import uuid

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db import models
from app import schemas
from app.db.models import BlackListTokens
from app.services.security import get_password_hash, decode_token


# =========== USER SECTION ===========
async def create_user(db: AsyncSession, user_in: schemas.UserRegister):
    raw_password = user_in.password.get_secret_value()
    hashed_password = get_password_hash(raw_password)

    db_user = models.User(
        email=user_in.email,
        full_name=user_in.full_name,
        password=hashed_password,
        role='member'
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


async def get_user_by_email(db: AsyncSession, email: str):
    stmt = select(models.User).where(models.User.email == email)
    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def add_token_to_blacklist(db: AsyncSession, token: str):
    payload = decode_token(token)
    exp_date = datetime.fromtimestamp(payload.get('exp'), tz=timezone.utc)

    blacklist_token = BlackListTokens(token=token, expire_at=exp_date)
    db.add(blacklist_token)
    await db.commit()

    return blacklist_token


async def get_blacklisted_token(db: AsyncSession, token: str):
    stmt = select(models.BlackListTokens).where(models.BlackListTokens.token == token)
    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def update_user_password(user: models.User, new_password: str, db: AsyncSession):
    hashed_password = get_password_hash(new_password)

    user.password = hashed_password

    db.add(user)
    await db.commit()
    await db.refresh(user)


# =========== USER SECTION ===========

# ====================================

# =========== TEAM SECTION ===========
async def create_team(name: str, db: AsyncSession, current_user: models.User):
    new_team = models.Team(
        name=name,
        invite_code=str(uuid.uuid4())
    )

    db.add(new_team)

    await db.flush()

    team_member = models.TeamMember(
        role='manager',
        user_id=current_user.id,
        team_id=new_team.id
    )
    db.add(team_member)

    await db.commit()
    await db.refresh(new_team)

    return new_team


async def get_team_by_team_id(team_id: int, db: AsyncSession, current_user: models.User):
    stmt = select(models.Team).where(models.Team.id == team_id).options(selectinload(models.Team.members))
    result = await db.execute(stmt)
    team = result.scalar_one_or_none()
    if not team:
        return None

    member_ids = [member.id for member in team.members]

    if current_user.role != 'manager' and current_user.id not in member_ids:
        return None
    return team


async def get_team_by_invite_code(invite_code: str, db: AsyncSession):
    stmt = select(models.Team).where(models.Team.invite_code == invite_code)
    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def add_member_to_team(current_user: models.User, team: models.Team, db: AsyncSession):
    new_member = models.TeamMember(
        role='member',
        user_id=current_user.id,
        team_id=team.id
    )

    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)

    return new_member


async def remove_member_from_team(team_id: int, user_id: int, db: AsyncSession, current_user: models.User):
    stmt = select(models.Team).where(models.Team.id == team_id).options(selectinload(models.Team.members))
    result = await db.execute(stmt)
    team = result.scalar_one_or_none()

    if not team:
        return None

    if current_user.role == 'manager':
        for member in team.members:
            if member.user_id == user_id:
                await db.delete(member)
                await db.commit()
                return team
    return None


async def update_members_role(
        team_id: int,
        user_id: int,
        new_role: str,
        db: AsyncSession,
        current_user: models.User):
    stmt = select(models.Team).where(models.Team.id == team_id).options(selectinload(models.Team.members))
    result = await db.execute(stmt)
    team = result.scalar_one_or_none()
    if not team:
        return None

    if current_user.role == 'manager':
        for member in team.members:
            if member.user_id == user_id:
                member.role = new_role
                await db.commit()
                await db.refresh(member)
                return member


# =========== TEAM SECTION ===========
# ====================================
# =========== TASK SECTION ===========
async def check_user_in_team(team_id: int, user_id: int, db: AsyncSession):
    stmt = (select(models.TeamMember).where(models.TeamMember.team_id == team_id)
            .where(models.TeamMember.user_id == user_id))
    result = await db.execute(stmt)
    members = result.scalar_one_or_none()
    return members


async def create_task(task_data: schemas.TaskCreate, db: AsyncSession, team_id: int):
    """
    Создание задачи
    """
    new_task = models.Task(
        title=task_data.title,
        description=task_data.description,
        due_date=task_data.due_date,
        user_id=task_data.user_id,
        team_id=team_id,
        status='To do'
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
    stmt = select(models.Task).where(models.Task.id == task_id, models.Task.team_id == team_id)
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
    task = await get_task_by_id(task_id=task_id, team_id=team_id, db=db)
    if not task:
        return None

    await db.delete(task)
    await db.commit()
    return True

# =========== TASK SECTION ===========
