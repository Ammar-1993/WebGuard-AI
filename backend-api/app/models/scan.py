"""
WebGuard AI — Scan Models (Pydantic Schemas)
==============================================
نماذج بيانات الفحص الأمني: الطلب، الحالة، والاستجابة.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class ScanStatus(str, Enum):
    """حالات الفحص الأمني المحتملة."""
    PENDING = "pending"           # في انتظار البدء
    SCANNING = "scanning"         # جاري الفحص بواسطة ZAP
    ANALYZING = "analyzing"       # جاري التحليل بواسطة الذكاء الاصطناعي
    COMPLETED = "completed"       # اكتمل بنجاح
    FAILED = "failed"             # فشل الفحص


class ScanRequest(BaseModel):
    """نموذج طلب فحص جديد — يُرسله المستخدم."""
    target_url: HttpUrl = Field(
        ...,
        description="رابط الموقع المراد فحصه أمنياً",
        examples=["https://example.com"],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "target_url": "https://example.com"
            }
        }


class ScanStatusResponse(BaseModel):
    """نموذج حالة الفحص — للاستعلام عن تقدم الفحص."""
    scan_id: str = Field(..., description="المُعرّف الفريد للفحص")
    status: ScanStatus = Field(..., description="الحالة الحالية للفحص")
    target_url: str = Field(..., description="الرابط المُفحص")
    progress: int = Field(
        default=0,
        ge=0,
        le=100,
        description="نسبة التقدم (0-100%)",
    )
    message: str = Field(default="", description="رسالة توضيحية عن الحالة")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="وقت إنشاء الفحص",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="وقت اكتمال الفحص",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "scan_id": "64f1a2b3c4d5e6f7a8b9c0d1",
                "status": "scanning",
                "target_url": "https://example.com",
                "progress": 45,
                "message": "جاري فحص الصفحات المكتشفة...",
                "created_at": "2024-01-15T10:30:00",
                "completed_at": None,
            }
        }
