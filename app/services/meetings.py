from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.core.datetime import normalize_datetime
from app.crud import meetings
from app.db import models


async def check_date(
        team_id: int,
        new_start: datetime,
        new_end: datetime,
        db: AsyncSession,
        meeting_id: Optional[int] = None
):
    stmt = select(models.Meeting).where(
        models.Meeting.team_id == team_id,
        new_start < models.Meeting.ends_at,
        new_end > models.Meeting.starts_at,
    )
    if meeting_id:
        # проверка по айди решает проблему редактирования. Без нее сломается логика создания встречи, т.к. функция будет
        # требовать айди запрашиваемой встречи, а для создания айди этой встречи еще не существует
        stmt = stmt.where(models.Meeting.id != meeting_id)

    result = await db.execute(stmt)
    return result.scalars().first()


def meeting_to_response(meeting: models.Meeting):
    return schemas.MeetingResponse(
        id=meeting.id,
        starts_at=meeting.starts_at,
        ends_at=meeting.ends_at,
        organizer_id=meeting.organizer_id,
        organizer_name=meeting.organizer.full_name,
        members=[
            schemas.MeetingMemberResponse(
                id=member.id,
                full_name=member.user.full_name
            )
            for member in meeting.team_meetings_details
        ]
    )


async def create_meeting(meeting_data, team_id: int, user_id: int, db: AsyncSession):
    start = normalize_datetime(meeting_data.starts_at)
    end = normalize_datetime(meeting_data.ends_at)

    new_meeting = await meetings.create_meeting(starts_at=start, ends_at=end, team_id=team_id, user_id=user_id, db=db)

    unique_members = set(meeting_data.member_ids or [])

    unique_members.add(user_id)

    await meetings.add_members(team_id=team_id, meeting_id=new_meeting.id, member_ids=unique_members, db=db)

    await db.commit()
    await db.refresh(new_meeting)

    return new_meeting


async def update_meeting(meeting_id: int, team_id: int, update_data: dict, db: AsyncSession):
    meeting = await meetings.get_meeting_by_id(meeting_id=meeting_id, team_id=team_id, db=db)

    if not meeting:
        return None

    if 'member_ids' in update_data:

        new_members = set(update_data.pop('member_ids'))

        old_members = {item.user_id for item in meeting.team_meetings_details}

        remove_ids = old_members - new_members
        add_ids = new_members - old_members

        if remove_ids:
            await meetings.remove_members(meeting_id=meeting_id, user_ids=remove_ids, db=db)

        if add_ids:
            await meetings.add_members(team_id=team_id, meeting_id=meeting_id, member_ids=add_ids, db=db            )

    return await meetings.update_meeting(meeting, update_data=update_data, db=db)
