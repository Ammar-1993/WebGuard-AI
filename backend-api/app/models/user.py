"""
WebGuard AI — User Models (Pydantic Schemas)
==============================================
نماذج بيانات المستخدم: التسجيل، تسجيل الدخول، والـ Token.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """نموذج تسجيل مستخدم جديد."""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username (3-50 characters)",
    )
    email: EmailStr = Field(..., description="Email")
    password: str = Field(
        ...,
        min_length=6,
        description="Password (at least 6 characters)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "email": "admin@webguard.ai",
                "password": "SecurePass123",
            }
        }


class UserLogin(BaseModel):
    """نموذج تسجيل الدخول."""
    email: EmailStr = Field(..., description="Email")
    password: str = Field(..., description="Password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@webguard.ai",
                "password": "SecurePass123",
            }
        }


class UserResponse(BaseModel):
    """بيانات المستخدم المُعادة (بدون كلمة المرور)."""
    id: str = Field(..., description="Unique ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email")
    created_at: datetime = Field(..., description="Registration date")


class TokenResponse(BaseModel):
    """استجابة تسجيل الدخول — تحتوي على JWT Token."""
    access_token: str = Field(..., description="JWT Token for authentication")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User data")
