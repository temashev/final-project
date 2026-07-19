from datetime import datetime, date

from pydantic import BaseModel, EmailStr, Field, ConfigDict, SecretStr, field_validator, model_validator
from typing import List, Literal, Optional


class UserRegister(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    password: SecretStr = Field(min_length=8)
    confirm_password: SecretStr = Field(min_length=8)

    @field_validator('password')
    @classmethod
    def passwords_strength(cls, value: SecretStr) -> SecretStr:
        secret_value = value.get_secret_value()
        if not any(c.isupper() for c in secret_value):
            raise ValueError('Пароль должен содержать как минимум одну заглавную букву.')
        if not any(c.isdigit() for c in secret_value):
            raise ValueError('Пароль должен содержать как минимум одну цифру.')
        return value

    @model_validator(mode='after')
    def passwords_match(self) -> 'UserRegister':
        if self.password.get_secret_value() != self.confirm_password.get_secret_value():
            raise ValueError('Пароли не совпадают.')
        return self


class EvaluationCreate(BaseModel):
    score: int = Field(ge=1, le=5)
    comment: str


class EvaluationResponse(BaseModel):
    score: int
    comment: str

    model_config = ConfigDict(from_attributes=True)


class UserRegisterResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class UserPublicResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(UserPublicResponse):
    avg_score: float
    evaluations: list["EvaluationResponse"]


class UserLogin(BaseModel):
    email: EmailStr
    password: SecretStr = Field(min_length=8)


class UserPasswordChange(BaseModel):
    old_password: SecretStr = Field(min_length=8)
    new_password: SecretStr = Field(min_length=8)
    confirm_new_password: SecretStr = Field(min_length=8)

    @field_validator('new_password')
    @classmethod
    def passwords_strength(cls, value: SecretStr) -> SecretStr:
        secret_value = value.get_secret_value()
        if not any(c.isupper() for c in secret_value):
            raise ValueError('Пароль должен содержать как минимум одну заглавную букву.')
        if not any(c.isdigit() for c in secret_value):
            raise ValueError('Пароль должен содержать как минимум одну цифру.')
        return value

    @model_validator(mode='after')
    def passwords_match(self) -> 'UserPasswordChange':
        if self.new_password.get_secret_value() != self.confirm_new_password.get_secret_value():
            raise ValueError('Пароли не совпадают.')
        return self


class UserProfileUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None


class TeamCreate(BaseModel):
    name: str


class TeamUserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class TeamMemberResponse(BaseModel):
    id: int
    role: str
    user_id: int
    team_id: int

    user: TeamUserResponse

    model_config = ConfigDict(from_attributes=True)


class TeamMembersResponse(BaseModel):
    id: int
    name: str
    invite_code: str
    members: list[TeamMemberResponse]

    model_config = ConfigDict(from_attributes=True)


class UpdateRoleRequest(BaseModel):
    role: Literal['manager', 'member']


class TaskCreate(BaseModel):
    title: str
    description: str
    due_date: date
    status: Literal['open', 'in_progress', 'done'] = 'open'


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = None


class CommentCreate(BaseModel):
    text: str


class CommentResponse(BaseModel):
    id: int
    text: str
    created_at: datetime
    username: str  # тут будет full_name

    model_config = ConfigDict(from_attributes=True)


class MeetingCreate(BaseModel):
    starts_at: datetime
    ends_at: datetime
    member_ids: Optional[list[int]] = None


class MeetingMemberResponse(BaseModel):
    id: int
    full_name: str

    model_config = ConfigDict(from_attributes=True)


class MeetingResponse(BaseModel):
    id: int
    starts_at: datetime
    ends_at: datetime
    members: list[MeetingMemberResponse] = Field(default_factory=list)
    organizer_id: int
    organizer_name: str

    model_config = ConfigDict(from_attributes=True)


class MeetingUpdate(BaseModel):
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    member_ids: Optional[list[int]] = Field(default=None, examples=[1, 2])


class CalendarMeetingResponse(BaseModel):
    id: int
    starts_at: datetime
    ends_at: datetime
    team_id: int
    team_name: str
    organizer_id: int
    organizer_name: str
    members: list[MeetingMemberResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
