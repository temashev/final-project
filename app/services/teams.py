from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud import teams
from app.crud.teams import check_is_user_team_manager
from app.db import models


async def check_users_in_team(team_id: int, user_ids: list[int], db: AsyncSession):
    """
    Вспомогательная функция для проверки находится ли НЕСКОЛЬКО юзеров в команде
    """
    stmt = select(models.TeamMember.user_id).where(
        models.TeamMember.team_id == team_id,
        models.TeamMember.user_id.in_(user_ids)
    )

    result = await db.execute(stmt)
    ids = set(result.scalars().all())
    return ids == set(user_ids)


async def get_team_by_team_id(team_id: int, db: AsyncSession, current_user: models.User):
    team = await teams.get_team_by_team_id(team_id=team_id, db=db)

    if not team:
        return None

    member_ids = [member.user_id for member in team.members]

    if current_user.role != 'manager' and current_user.id not in member_ids:
        return None

    return team


async def create_team(name: str, db: AsyncSession, current_user: models.User):
    return await teams.create_team(name=name, db=db, current_user=current_user)


async def add_member_to_team(current_user: models.User, team: models.Team, db: AsyncSession):
    return await teams.add_member_to_team(current_user=current_user, team=team, db=db)


async def remove_member_from_team(team_id: int, user_id: int, db: AsyncSession, current_user: models.User):
    team = await teams.get_team_by_team_id(team_id=team_id, db=db)

    if not team:
        return None

    is_manager = await check_is_user_team_manager(team_id=team_id, user_id=current_user.id, db=db)

    if not is_manager:
        return None

    member_to_remove = next((m for m in team.members if m.user_id == user_id), None)

    if not member_to_remove:
        return None

    await teams.remove_member_from_team(member=member_to_remove, db=db)

    return team


async def update_members_role(team_id: int, user_id: int, new_role: str, db: AsyncSession, current_user: models.User):
    if current_user.role != 'manager':
        return None

    stmt = select(models.Team).where(models.Team.id == team_id).options(selectinload(models.Team.members))
    result = await db.execute(stmt)

    team = result.scalar_one_or_none()
    if not team:
        return None

    target_member = next((m for m in team.members if m.user_id == user_id), None)
    if not target_member:
        return None

    if target_member.role == 'manager' and new_role == 'member':
        managers_count = sum(1 for m in team.members if m.role == 'manager')

        if managers_count <= 1:
            raise HTTPException(
                status_code=400,
                detail='Нельзя понизить последнего менеджера. В команде должен остаться хотя бы один'
            )

    return await teams.update_members_role(member=target_member, new_role=new_role, db=db)


async def leave_team(team_id: int, user_id: int, db: AsyncSession):
    stmt_role = select(models.TeamMember.role).where(
        models.TeamMember.team_id == team_id,
        models.TeamMember.user_id == user_id
    )
    user_role = await db.scalar(stmt_role)

    if user_role == 'manager':
        stmt_count = select(func.count()).select_from(models.TeamMember).where(
            models.TeamMember.team_id == team_id,
            models.TeamMember.role == 'manager'
        )
        managers_count = await db.scalar(stmt_count)

        if managers_count <= 1:
            raise HTTPException(status_code=400, detail='Нельзя покинуть команду, так как вы последний менеджер')
    return await teams.leave_team(team_id=team_id, user_id=user_id, db=db)
