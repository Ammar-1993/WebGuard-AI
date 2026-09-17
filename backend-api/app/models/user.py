"""
WebGuard AI — User Models (Pydantic Schemas)
==============================================
نماذج بيانات المستخدم: التسجيل، تسجيل الدخول، والـ Token.

ملاحظة أمنية (Security Review — البند 4):
  كلمة المرور السابقة كانت تقبل 6 أحرف بلا أي شرط تعقيد، مما يجعل
  الحسابات عرضة للتخمين (خصوصًا مع غياب Rate Limiting سابقًا — تم
  إصلاحه في البند 3). السياسة الجديدة: 8 أحرف على الأقل، رقم واحد
  على الأقل، وحرف كبير واحد على الأقل.

  كما أُضيف حد أعلى (max_length=72) لأن bcrypt (المستخدم في
  core/security.py) يتعامل فعليًا مع أول 72 byte فقط من كلمة المرور —
  انظر التعليق الموجود في requirements.txt بخصوص تثبيت إصدار bcrypt
  لهذا السبب تحديدًا. رفض القيم الأطول من ذلك عند الإدخال أوضح
  للمستخدم من فشل صامت أو خطأ غير متوقع لاحقًا داخل passlib.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


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
        min_length=8,
        max_length=72,  # bcrypt يتجاهل ما بعد أول 72 byte — انظر الملاحظة أعلاه
        description=(
            "Password (min 8 characters, must include at least one digit "
            "and one uppercase letter)"
        ),
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """يتحقق من تعقيد كلمة المرور — لا يكفي الطول وحده."""
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v

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