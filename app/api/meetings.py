from datetime import datetime, timezone, date

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import check_is_user_team_manager, check_date, create_meeting, check_user_in_team, get_meetings_by_team, \
    delete_meeting, update_meeting, get_meeting_by_id, normalize_datetime, check_users_in_team, meeting_to_response, \
    get_calendar
from app.db.database import get_db_session
from app.dependencies import get_current_user
from app.schemas import MeetingResponse, MeetingUpdate, MeetingCreate, MeetingMemberResponse

meet_router = APIRouter(prefix='/teams', tags=['Встречи'])


@meet_router.post('/{team_id}/meetings/', response_model=MeetingResponse)
async def add_meeting(
        meeting_data: MeetingCreate,
        team_id: int = Path(le=2147483647, ge=1),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    manager = await check_is_user_team_manager(team_id=team_id, user_id=current_user.id, db=db)
    if not manager:
        raise HTTPException(status_code=403, detail='У вас нет доступа ко встречам команды')

    if meeting_data.member_ids:
        if not await check_users_in_team(team_id=team_id, user_ids=meeting_data.member_ids, db=db):
            raise HTTPException(status_code=400, detail='Некоторые участники не состоят в команде')

    start = normalize_datetime(meeting_data.starts_at)
    end = normalize_datetime(meeting_data.ends_at)

    if start >= end:
        raise HTTPException(status_code=400, detail="Время начала должно быть раньше времени окончания")

    if start <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Встреча не может быть запланирована в прошлом")

    check_meet = await check_date(team_id=team_id, new_start=start, new_end=end, db=db)
    if check_meet:
        raise HTTPException(status_code=403, detail='На это время уже запланирована встреча')

    new_meeting = await create_meeting(team_id=team_id, user_id=current_user.id, db=db, meeting_data=meeting_data)
    meeting = await get_meeting_by_id(
        meeting_id=new_meeting.id,
        team_id=team_id,
        db=db
    )

    return meeting_to_response(meeting)


@meet_router.get('/{team_id}/meetings/', response_model=list[MeetingResponse])
async def list_meetings(
        team_id: int = Path(le=2147483647, ge=1),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    member = await check_user_in_team(team_id=team_id, user_id=current_user.id, db=db)

    if not member:
        raise HTTPException(status_code=403, detail='У вас нет доступа ко встречам команды')

    meetings = await get_meetings_by_team(team_id=team_id, db=db)
    return meetings


@meet_router.delete('/{team_id}/meetings/{meeting_id}/')
async def meeting_delete(
        team_id: int = Path(le=2147483647, ge=1),
        meeting_id: int = Path(le=2147483647, ge=1),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    manager = await check_is_user_team_manager(team_id=team_id, user_id=current_user.id, db=db)
    if not manager:
        raise HTTPException(status_code=403, detail='У вас нет доступа ко встречам команды')

    meeting = await delete_meeting(team_id=team_id, meeting_id=meeting_id, db=db)
    if not meeting:
        raise HTTPException(status_code=404, detail=f'Встречи с id:{meeting_id} не существует')
    return {'detail': 'Встреча успешно удалена'}


@meet_router.patch('/{team_id}/meetings/{meeting_id}/', response_model=MeetingResponse)
async def meeting_update(
        updated_data: MeetingUpdate,
        team_id: int = Path(le=2147483647, ge=1),
        meeting_id: int = Path(le=2147483647, ge=1),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    manager = await check_is_user_team_manager(team_id=team_id, user_id=current_user.id, db=db)
    if not manager:
        raise HTTPException(status_code=403, detail='У вас нет доступа ко встречам команды')

    meeting = await get_meeting_by_id(meeting_id=meeting_id, team_id=team_id, db=db)
    if not meeting:
        raise HTTPException(status_code=404, detail='Встреча не найдена')

    updated_dict = updated_data.model_dump(exclude_unset=True)

    new_start = updated_dict.get('starts_at', meeting.starts_at)
    new_end = updated_dict.get('ends_at', meeting.ends_at)
    if new_start >= new_end:
        raise HTTPException(status_code=400, detail='Время начала должно быть раньше времени окончания')
    if new_start <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail='Встреча не может быть запланирована в прошлом')

    check_meet = await check_date(meeting_id=meeting_id, team_id=team_id, new_start=new_start, new_end=new_end, db=db)
    if check_meet:
        raise HTTPException(status_code=403, detail='На это время уже запланирована встреча')

    updated_meeting = await update_meeting(meeting_id=meeting_id, team_id=team_id, update_data=updated_dict, db=db)

    if not updated_meeting:
        raise HTTPException(
            status_code=404,
            detail='Встреча не найдена, ее нет в списке или у вас недостаточно прав'
        )

    return MeetingResponse(
        id=updated_meeting.id,
        starts_at=updated_meeting.starts_at,
        ends_at=updated_meeting.ends_at,
        members=[member.user for member in updated_meeting.team_meetings_details],
        organizer_id=updated_meeting.organizer_id,
        organizer_name=updated_meeting.organizer.full_name
    )


@meet_router.get('/{team_id}/calendar/', response_model=list[MeetingResponse])
async def calendar(
        team_id: int = Path(le=2147483647, ge=1),
        from_date: date = Query(..., alias='from'),
        to_date: date = Query(..., alias='to'),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    manager = await check_user_in_team(team_id=team_id, user_id=current_user.id, db=db)

    if not manager:
        raise HTTPException(status_code=403, detail='У вас нет доступа к календарю команды')

    if from_date >= to_date:
        raise HTTPException(status_code=400, detail='Некорректный диапазон дат')

    meetings = await get_calendar(team_id=team_id, from_date=from_date, to_date=to_date, db=db)

    return [MeetingResponse(
        id=meeting.id,
        starts_at=meeting.starts_at,
        ends_at=meeting.ends_at,
        organizer_id=meeting.organizer_id,
        organizer_name=meeting.organizer.full_name,
        members=[MeetingMemberResponse(
            id=item.user.id,
            full_name=item.user.full_name
        ) for item in meeting.team_meetings_details]
    ) for meeting in meetings]
