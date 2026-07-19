import uuid

from datetime import datetime, timezone, date
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists, delete, func, or_
from sqlalchemy.orm import selectinload

from app.db import models
from app import schemas
from app.db.models import BlackListTokens, Meeting
from app.services.security import get_password_hash, decode_token


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


async def check_user_in_team(team_id: int, user_id: int, db: AsyncSession):
    """
    Вспомогательная функция для проверки находится ли ОДИН юзер в команде
    """
    stmt = select(
        exists().where(
            models.TeamMember.team_id == team_id,
            models.TeamMember.user_id == user_id
        )
    )
    result = await db.execute(stmt)

    return result.scalar()


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


def normalize_datetime(dt: datetime) -> datetime:
    """
    Вспомогательная функция для нормализации времени, чтобы не указывать часовые пояса вручную
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


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


async def update_user_profile(user: models.User, updated_data: dict, db: AsyncSession):
    """
    Обновление профиля юзера
    """
    if not user:
        return None

    for k, v in updated_data.items():
        setattr(user, k, v)

    await db.commit()
    await db.refresh(user)
    return user


async def get_user_profile_data(user_id: int, db: AsyncSession):
    stmt = select(models.User).where(
        models.User.id == user_id
    ).options(selectinload(models.User.tasks).selectinload(models.Task.evaluation))
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
    stmt = select(models.Team).where(models.Team.id == new_team.id).options(
        selectinload(models.Team.members).selectinload(models.TeamMember.user)
    )

    result = await db.execute(stmt)
    return result.scalar_one()


async def get_team_by_team_id(team_id: int, db: AsyncSession, current_user: models.User):
    stmt = select(models.Team).where(models.Team.id == team_id).options(
        selectinload(models.Team.members).selectinload(models.TeamMember.user)
    )
    result = await db.execute(stmt)
    team = result.scalar_one_or_none()
    if not team:
        return None

    member_ids = [member.user_id for member in team.members]

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
    stmt = (
        select(models.Team)
        .where(models.Team.id == team_id)
        .options(
            selectinload(models.Team.members).joinedload(models.TeamMember.user)
        )
    )
    result = await db.execute(stmt)
    team = result.scalar_one_or_none()

    if not team:
        return None

    is_manager = any(m.user_id == current_user.id and m.role == 'manager' for m in team.members)
    if not is_manager:
        return None

    member_to_remove = next((m for m in team.members if m.user_id == user_id), None)
    if member_to_remove:
        await db.delete(member_to_remove)
        await db.commit()
        await db.refresh(team)
        team.members = [member.user for member in team.members if member.user_id != user_id]
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


async def leave_team(team_id: int, user_id: int, db: AsyncSession):
    stmt = delete(models.TeamMember).where(
        models.TeamMember.team_id == team_id,
        models.TeamMember.user_id == user_id
    )
    result = await db.execute(stmt)
    await db.commit()

    return result.rowcount > 0


# =========== TEAM SECTION ===========
# ====================================
# =========== TASK SECTION ===========
async def create_task(task_data: schemas.TaskCreate, db: AsyncSession, team_id: int, user_id: int):
    """
    Создание задачи
    """
    new_task = models.Task(
        title=task_data.title,
        description=task_data.description,
        due_date=task_data.due_date,
        user_id=user_id,
        team_id=team_id,
        status=task_data.status
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
    stmt = select(models.Task).where(
        models.Task.id == task_id, models.Task.team_id == team_id
    ).options(selectinload(models.Task.evaluation))
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
    """
    Удаление задачи
    """
    task = await get_task_by_id(task_id=task_id, team_id=team_id, db=db)
    if not task:
        return None

    await db.delete(task)
    await db.commit()
    return True


async def create_comment(
        comment_data: schemas.CommentCreate,
        db: AsyncSession,
        team_id: int,
        task_id: int,
        user_id: int
):
    """
    Создание комментария
    """
    stmt = select(models.Task).where(
        models.Task.id == task_id,
        models.Task.team_id == team_id
    )

    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if not task:
        return None

    new_comment = models.Comment(
        text=comment_data.text,
        created_at=datetime.now(),
        user_id=user_id,
        team_id=team_id,
        task_id=task_id
    )

    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)

    return new_comment


async def show_comments_list(task_id: int, team_id: int, db: AsyncSession):
    stmt = select(models.Comment).where(
        models.Comment.team_id == team_id, models.Comment.task_id == task_id
    ).options(selectinload(models.Comment.user))
    result = await db.execute(stmt)
    comments = result.scalars().all()
    full_response = [
        schemas.CommentResponse(
            id=comment.id,
            text=comment.text,
            created_at=comment.created_at,
            username=comment.user.full_name
        ) for comment in comments
    ]
    return full_response


async def create_evaluation(
        task_id: int,
        team_id: int,
        eval_data: schemas.EvaluationCreate,
        db: AsyncSession
):
    task = await get_task_by_id(task_id=task_id, team_id=team_id, db=db)

    if task.evaluation:
        task.evaluation.score = eval_data.score
        task.evaluation.comment = eval_data.comment
        await db.commit()
        return task.evaluation

    new_evaluation = models.Evaluation(
        score=eval_data.score,
        comment=eval_data.comment,
        task_id=task_id
    )

    db.add(new_evaluation)
    await db.commit()
    await db.refresh(new_evaluation)
    return new_evaluation


# =========== TASK SECTION ===========
# ====================================
# ========= MEETINGS SECTION =========
async def check_date(
        team_id: int,
        new_start: datetime,
        new_end: datetime,
        db: AsyncSession,
        meeting_id: Optional[int] = None
):
    stmt = select(models.Meeting).where(
        Meeting.team_id == team_id,
        new_start < Meeting.ends_at,
        new_end > Meeting.starts_at,
    )
    if meeting_id:
        # проверка по айди решает проблему редактирования. Без нее сломается логика создания встречи, т.к. функция будет
        # требовать айди запрашиваемой встречи, а для создания айди этой встречи еще не существует
        stmt = stmt.where(Meeting.id != meeting_id)
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


async def create_meeting(
        meeting_data: schemas.MeetingCreate,
        team_id: int,
        user_id: int,
        db: AsyncSession
):
    start = normalize_datetime(meeting_data.starts_at)
    end = normalize_datetime(meeting_data.ends_at)

    new_meeting = models.Meeting(
        starts_at=start,
        ends_at=end,
        organizer_id=user_id,
        team_id=team_id
    )

    db.add(new_meeting)
    await db.flush()

    unique_members = set(meeting_data.member_ids or [])
    unique_members.add(user_id)

    if meeting_data.member_ids:
        add_stmt = [
            models.TeamMeetings(
                team_id=team_id,
                meeting_id=new_meeting.id,
                user_id=member_id,
            ) for member_id in unique_members
        ]
        db.add_all(add_stmt)

    await db.commit()
    await db.refresh(new_meeting)

    return new_meeting


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
    meetings = result.scalars().all()
    return [meeting_to_response(meeting) for meeting in meetings]


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


async def delete_meeting(team_id: int, meeting_id: int, db: AsyncSession):
    """
    Удаление встречи
    """
    meeting = await get_meeting_by_id(meeting_id=meeting_id, team_id=team_id, db=db)
    if not meeting:
        return None

    await db.delete(meeting)
    await db.commit()
    return True


async def update_meeting(meeting_id: int, team_id: int, update_data: dict, db: AsyncSession):
    """
    Обновление встречи
    """
    meeting = await get_meeting_by_id(meeting_id=meeting_id, team_id=team_id, db=db)
    if not meeting:
        return None

    if 'member_ids' in update_data:
        new_members = set(update_data.pop('member_ids'))

        old_members = {item.user_id for item in meeting.team_meetings_details}

        remove_ids = old_members - new_members
        add_ids = new_members - old_members

        if remove_ids:
            await db.execute(delete(models.TeamMeetings).where(
                models.TeamMeetings.meeting_id == meeting_id,
                models.TeamMeetings.user_id.in_(remove_ids)
            ))
        for user_id in add_ids:
            db.add(models.TeamMeetings(
                meeting_id=meeting_id,
                team_id=team_id,
                user_id=user_id
            ))

    for k, v in update_data.items():
        setattr(meeting, k, v)

    await db.commit()

    return await get_meeting_by_id(
        meeting_id=meeting_id,
        team_id=team_id,
        db=db
    )


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

# ========= MEETINGS SECTION =========
