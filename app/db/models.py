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
    meetings: Mapped[list['Meeting']] = relationship(back_populates='user')


class Team(Base):
    __tablename__ = 'teams'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    invite_code: Mapped[str] = mapped_column(String)

    members: Mapped[list['TeamMember']] = relationship(back_populates='team')
    tasks: Mapped[list['Task']] = relationship(back_populates='team')
    meetings: Mapped[list['Meeting']] = relationship(back_populates='team')


class Task(Base):
    __tablename__ = 'tasks'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    due_date: Mapped[date] = mapped_column(Date)

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    team_id: Mapped[int] = mapped_column(ForeignKey('teams.id'))

    user: Mapped['User'] = relationship(back_populates='tasks')
    team: Mapped['Team'] = relationship(back_populates='tasks')

    evaluation: Mapped['Evaluation | None'] = relationship(back_populates='task')


class Meeting(Base):
    __tablename__ = 'meetings'

    id: Mapped[int] = mapped_column(primary_key=True)
    starts_at: Mapped[datetime]  = mapped_column(DateTime)
    ends_at: Mapped[datetime]  = mapped_column(DateTime)

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    team_id: Mapped[int] = mapped_column(ForeignKey('teams.id'))

    user: Mapped['User'] = relationship(back_populates='meetings')
    team: Mapped['Team'] = relationship(back_populates='meetings')


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