from datetime import date, datetime

from sqlalchemy import select, delete, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import models


async def create_meeting(starts_at: datetime, ends_at: datetime, team_id: int, user_id: int, db: AsyncSession):
    new_meeting = models.Meeting(
        starts_at=starts_at,
        ends_at=ends_at,
        organizer_id=user_id,
        team_id=team_id
    )

    db.add(new_meeting)
    await db.flush()

    return new_meeting


async def add_members(team_id: int, meeting_id: int, member_ids: set[int], db: AsyncSession):
    add_stmt = [
        models.TeamMeetings(
            team_id=team_id,
            meeting_id=meeting_id,
            user_id=member_id,
        )
        for member_id in member_ids
    ]

    db.add_all(add_stmt)


async def get_meetings_by_team(team_id: int, db: AsyncSession):
    """
    Получение всех встреч команды
    """
    stmt = select(models.Meeting).where(models.Meeting.team_id == team_id).options(
        selectinload(models.Meeting.organizer),
        selectinload(models.Meeting.team_meetings_details)
        .selectinload(models.TeamMeetings.user)
    )

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_meeting_by_id(meeting_id: int, team_id: int, db: AsyncSession):
    """
    Получение встречи по айди
    """
    stmt = select(models.Meeting).where(
        models.Meeting.id == meeting_id,
        models.Meeting.team_id == team_id
    ).options(
        selectinload(models.Meeting.organizer),
        selectinload(models.Meeting.team_meetings_details).selectinload(models.TeamMeetings.user)
    )

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def delete_meeting(meeting, db: AsyncSession):
    """
    Удаление встречи
    """

    await db.delete(meeting)
    await db.commit()
    return True


async def update_meeting(meeting, update_data: dict, db: AsyncSession):
    """
    Обновление встречи
    """
    for k, v in update_data.items():
        setattr(meeting, k, v)

    await db.commit()

    return meeting


async def remove_members(meeting_id: int, user_ids: set[int], db: AsyncSession):
    stmt = delete(models.TeamMeetings).where(
        models.TeamMeetings.meeting_id == meeting_id,
        models.TeamMeetings.user_id.in_(user_ids)
    )

    await db.execute(stmt)


async def get_calendar(user_id: int, from_date: date, to_date: date, db: AsyncSession):
    stmt = select(models.Meeting).where(
        func.date(models.Meeting.starts_at) >= from_date,
        func.date(models.Meeting.starts_at) <= to_date,
        or_(
            models.Meeting.organizer_id == user_id,
            models.Meeting.team_meetings_details.any(models.TeamMeetings.user_id == user_id)
        )
    ).options(
        selectinload(models.Meeting.organizer),
        selectinload(models.Meeting.team),
        selectinload(models.Meeting.team_meetings_details)
        .selectinload(models.TeamMeetings.user)
    ).order_by(models.Meeting.starts_at)

    result = await db.execute(stmt)
    return result.scalars().unique().all()
