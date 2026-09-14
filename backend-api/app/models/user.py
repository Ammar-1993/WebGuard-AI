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
        description="اسم المستخدم (3-50 حرف)",
    )
    email: EmailStr = Field(..., description="البريد الإلكتروني")
    password: str = Field(
        ...,
        min_length=6,
        description="كلمة المرور (6 أحرف على الأقل)",
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
    email: EmailStr = Field(..., description="البريد الإلكتروني")
    password: str = Field(..., description="كلمة المرور")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@webguard.ai",
                "password": "SecurePass123",
            }
        }


class UserResponse(BaseModel):
    """بيانات المستخدم المُعادة (بدون كلمة المرور)."""
    id: str = Field(..., description="المُعرّف الفريد")
    username: str = Field(..., description="اسم المستخدم")
    email: str = Field(..., description="البريد الإلكتروني")
    created_at: datetime = Field(..., description="تاريخ التسجيل")


class TokenResponse(BaseModel):
    """استجابة تسجيل الدخول — تحتوي على JWT Token."""
    access_token: str = Field(..., description="JWT Token للمصادقة")
    token_type: str = Field(default="bearer", description="نوع الـ Token")
    user: UserResponse = Field(..., description="بيانات المستخدم")
