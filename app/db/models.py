## TODO: ИНДЕКСЫ!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
from datetime import datetime, date

from sqlalchemy import ForeignKey, String, Integer, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class TeamMember(Base):
    __tablename__ = 'team_member'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role: Mapped[str] = mapped_column(String, default='member')

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    team_id: Mapped[int] = mapped_column(ForeignKey('teams.id'))

    user: Mapped['User'] = relationship(back_populates='team_membership')
    team: Mapped['Team'] = relationship(back_populates='members')


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    full_name: Mapped[str] = mapped_column(String)
    password: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)

    team_membership: Mapped[list['TeamMember']] = relationship(back_populates='user')
    tasks: Mapped[list['Task']] = relationship(back_populates='user')
    comments: Mapped[list['Comment']] = relationship(back_populates='user')
    organized_meetings: Mapped[list['Meeting']] = relationship(back_populates='organizer')
    team_meetings_details: Mapped[list['TeamMeetings']] = relationship(back_populates='user',
                                                                       cascade='all, delete-orphan')


class Team(Base):
    __tablename__ = 'teams'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    invite_code: Mapped[str] = mapped_column(String)

    members: Mapped[list['TeamMember']] = relationship(back_populates='team', cascade='all, delete-orphan')
    tasks: Mapped[list['Task']] = relationship(back_populates='team', cascade='all, delete-orphan')
    comments: Mapped[list['Comment']] = relationship(back_populates='team', cascade='all, delete-orphan')
    meetings: Mapped[list['Meeting']] = relationship(back_populates='team', cascade='all, delete-orphan')

    team_meetings_details: Mapped[list['TeamMeetings']] = relationship(back_populates='team',
                                                                       cascade='all, delete-orphan')


class Task(Base):
    __tablename__ = 'tasks'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default='open')
    due_date: Mapped[date] = mapped_column(Date)

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    team_id: Mapped[int] = mapped_column(ForeignKey('teams.id'))

    user: Mapped['User'] = relationship(back_populates='tasks')
    team: Mapped['Team'] = relationship(back_populates='tasks')
    comments: Mapped[list['Comment']] = relationship(back_populates='task', cascade='all, delete-orphan')

    evaluation: Mapped['Evaluation | None'] = relationship(back_populates='task')


class Comment(Base):
    __tablename__ = 'comments'

    id: Mapped[int] = mapped_column(primary_key=True)

    text: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    team_id: Mapped[int] = mapped_column(ForeignKey('teams.id'))
    task_id: Mapped[int] = mapped_column(ForeignKey('tasks.id'))

    user: Mapped['User'] = relationship(back_populates='comments')
    team: Mapped['Team'] = relationship(back_populates='comments')
    task: Mapped['Task'] = relationship(back_populates='comments')


class TeamMeetings(Base):
    __tablename__ = 'team_meetings'

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    team_id: Mapped[int] = mapped_column(ForeignKey('teams.id'))
    meeting_id: Mapped[int] = mapped_column(ForeignKey('meetings.id'))

    user: Mapped['User'] = relationship(back_populates='team_meetings_details')
    team: Mapped['Team'] = relationship(back_populates='team_meetings_details')
    meeting: Mapped['Meeting'] = relationship(back_populates='team_meetings_details')


class Meeting(Base):
    __tablename__ = 'meetings'

    id: Mapped[int] = mapped_column(primary_key=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    organizer_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    team_id: Mapped[int] = mapped_column(ForeignKey('teams.id'))

    organizer: Mapped['User'] = relationship(back_populates='organized_meetings')
    team: Mapped['Team'] = relationship(back_populates='meetings')
    team_meetings_details: Mapped[list['TeamMeetings']] = relationship(back_populates='meeting',
                                                                       cascade='all, delete-orphan')


class Evaluation(Base):
    __tablename__ = 'evaluations'

    id: Mapped[int] = mapped_column(primary_key=True)
    score: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(String)

    task_id: Mapped[int] = mapped_column(ForeignKey('tasks.id'), unique=True)

    task: Mapped['Task'] = relationship(back_populates='evaluation')


class BlackListTokens(Base):
    __tablename__ = 'blacklist_tokens'

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String)
    expire_at: Mapped[datetime] = mapped_column(DateTime)
