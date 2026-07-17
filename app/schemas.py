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


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


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


class TeamMembers(BaseModel):
    name: str
    invite_code: str
    members: List['UserResponse']


class UpdateRoleRequest(BaseModel):
    role: Literal['manager', 'member']


class TaskCreate(BaseModel):
    title: str
    description: str
    due_date: date
    user_id: int


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    user_id: Optional[int] = None
    status: Optional[str] = None


class CommentCreate(BaseModel):
    text: str


class CommentResponse(BaseModel):
    id: int
    text: str
    created_at: datetime
    username: str   # тут будет full_name