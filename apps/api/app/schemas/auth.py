from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class UserPublic(BaseModel):
    id: str
    email: EmailStr | None = None
    username: str | None = None


class SignupRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class AuthResponse(BaseModel):
    user: UserPublic


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetRequestResponse(BaseModel):
    ok: bool = True
    # Returned only in non-prod/test/dev for convenience.
    reset_token: str | None = None


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=8, max_length=512)
    new_password: str = Field(min_length=8, max_length=256)


class PasswordResetConfirmResponse(BaseModel):
    ok: bool = True
