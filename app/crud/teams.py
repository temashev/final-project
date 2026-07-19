import uuid

from sqlalchemy import select, exists, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import models


async def check_is_user_team_manager(team_id: int, user_id: int, db: AsyncSession):
    """
    Вспомогательная функция для проверки является ли юзер менеджером этой команды
    """
    stmt = select(
        exists().where(
            models.TeamMember.team_id == team_id,
            models.TeamMember.user_id == user_id,
            models.TeamMember.role == 'manager'
        )
    )
    result = await db.execute(stmt)

    return result.scalar()


async def check_user_in_team(team_id: int, user_id: int, db: AsyncSession):
    """
    Вспомогательная функция для проверки находится ли ОДИН юзер в команде
    """
    stmt = select(exists().where(models.TeamMember.team_id == team_id, models.TeamMember.user_id == user_id))
    result = await db.execute(stmt)

    return result.scalar()


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
    stmt = select(models.Team).where(models.Team.id == new_team.id).options(
        selectinload(models.Team.members).selectinload(models.TeamMember.user)
    )

    result = await db.execute(stmt)
    return result.scalar_one()


async def get_team_by_team_id(team_id: int, db: AsyncSession):
    stmt = select(models.Team).where(models.Team.id == team_id).options(
        selectinload(models.Team.members).selectinload(models.TeamMember.user)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


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


async def remove_member_from_team(member: models.TeamMember, db: AsyncSession):
    await db.delete(member)
    await db.commit()


async def update_members_role(member: models.TeamMember, new_role: str, db: AsyncSession):
    member.role = new_role

    await db.commit()
    await db.refresh(member)

    return member


async def leave_team(team_id: int, user_id: int, db: AsyncSession):
    stmt = delete(models.TeamMember).where(
        models.TeamMember.team_id == team_id,
        models.TeamMember.user_id == user_id
    )
    result = await db.execute(stmt)
    await db.commit()

    return result.rowcount > 0
