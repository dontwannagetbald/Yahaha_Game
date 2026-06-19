from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: Optional[str] = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    user_id: str
    email: Optional[str]
    display_name: Optional[str]
    avatar_url: Optional[str]


class AuthResponse(BaseModel):
    user: UserResponse


class OAuthStartResponse(BaseModel):
    authorization_url: str


class MessageResponse(BaseModel):
    message: str
