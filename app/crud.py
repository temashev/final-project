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
    if not team or current_user not in team.members:
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
            if member.id == user_id:
                team.members.remove(member)
                await db.commit()
                return team
    return None

# =========== TEAM SECTION ===========
