from typing import Optional
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str


class UserInDB(User):
    hashed_password: str
    preferred_language: dict
    preferred_style: dict
    role: str


class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr


class UserDeleteRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
