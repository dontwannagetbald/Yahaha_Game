from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: Optional[str] = Field(default=None, max_length=120)
    avatar_url: Optional[str] = Field(default=None, max_length=2048)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        has_letter = any(character.isalpha() for character in value)
        has_digit = any(character.isdigit() for character in value)
        if not has_letter or not has_digit:
            raise ValueError("Password must include both letters and numbers")
        return value


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


class AvatarUploadPresignRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(gt=0)


class AvatarUploadPresignResponse(BaseModel):
    upload_id: str
    object_key: str
    upload_url: str
    expires_in: int


class AvatarUploadCompleteRequest(BaseModel):
    upload_id: str
    object_key: str = Field(min_length=1)
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(gt=0)


class AvatarUploadCompleteResponse(BaseModel):
    avatar_url: str


class MessageResponse(BaseModel):
    message: str


class UploadPresignRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(gt=0)


class UploadPresignResponse(BaseModel):
    upload_id: str
    object_key: str
    upload_url: str
    expires_in: int


class UploadCompleteRequest(BaseModel):
    upload_id: str
    object_key: str = Field(min_length=1)
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(gt=0)


class UploadCompleteResponse(BaseModel):
    asset_id: str
    filename: str
    mime_type: str
    size_bytes: int
