"""
WebGuard AI — Report Models (Pydantic Schemas)
================================================
نماذج بيانات التقارير: الثغرات، تحليل الذكاء الاصطناعي، مؤشر الأمان، والتقرير الكامل.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """مستويات خطورة الثغرات الأمنية (حسب تصنيف OWASP ZAP)."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFORMATIONAL = "Informational"


class SecurityGrade(str, Enum):
    """التقديرات الأمنية بناءً على مؤشر الأمان."""
    A_PLUS = "A+"   # 95-100: ممتاز
    A = "A"          # 85-94: جيد جداً
    B = "B"          # 70-84: جيد
    C = "C"          # 50-69: متوسط
    D = "D"          # 30-49: ضعيف
    F = "F"          # 0-29: خطير


# ─── الثغرة الأمنية الخام (من ZAP) ───

class Vulnerability(BaseModel):
    """ثغرة أمنية فردية كما يُبلّغ عنها محرك OWASP ZAP."""
    name: str = Field(..., description="اسم الثغرة الأمنية")
    risk: RiskLevel = Field(..., description="مستوى الخطورة")
    confidence: str = Field(default="Medium", description="مستوى الثقة في النتيجة")
    description: str = Field(default="", description="الوصف التقني للثغرة")
    solution: str = Field(default="", description="الحل المقترح من ZAP")
    url: str = Field(default="", description="الرابط المصاب بالثغرة")
    cweid: str = Field(default="", description="معرّف CWE الدولي")
    wascid: str = Field(default="", description="معرّف WASC")
    evidence: str = Field(default="", description="الدليل/البرهان على وجود الثغرة")
    reference: str = Field(default="", description="مراجع إضافية")


# ─── تحليل الذكاء الاصطناعي لثغرة واحدة ───

class AIVulnerabilityAnalysis(BaseModel):
    """تحليل الذكاء الاصطناعي لثغرة أمنية واحدة."""
    original_name: str = Field(..., description="اسم الثغرة الأصلي من ZAP")
    risk: RiskLevel = Field(..., description="مستوى الخطورة")
    is_false_positive: bool = Field(
        default=False,
        description="هل هي إنذار خاطئ (False Positive)؟",
    )
    false_positive_reason: str = Field(
        default="",
        description="سبب اعتبارها إنذاراً خاطئاً (إن وُجد)",
    )
    simplified_description: str = Field(
        ...,
        description="وصف مبسّط ومفهوم للثغرة (بلغة المطوّر)",
    )
    impact: str = Field(
        default="",
        description="التأثير المحتمل لهذه الثغرة على النظام",
    )
    remediation_steps: List[str] = Field(
        default_factory=list,
        description="خطوات الإصلاح المقترحة",
    )
    remediation_code: str = Field(
        default="",
        description="كود الإصلاح الجاهز للتطبيق",
    )
    code_language: str = Field(
        default="",
        description="لغة كود الإصلاح (Python, JavaScript, PHP, إلخ)",
    )


# ─── مؤشر الأمان (Security Score) ───

class SecurityScore(BaseModel):
    """
    مؤشر الأمان المحسوب — متطلب الدكتور المشرف.
    يبدأ من 100 ويُخصم منه حسب خطورة الثغرات.
    """
    score: int = Field(
        ...,
        ge=0,
        le=100,
        description="الدرجة الرقمية (0-100)",
    )
    grade: SecurityGrade = Field(..., description="التقدير الحرفي (A+ إلى F)")
    color: str = Field(..., description="لون المؤشر (#hex)")
    label: str = Field(..., description="وصف نصي مختصر للحالة")
    breakdown: dict = Field(
        default_factory=dict,
        description="تفصيل الخصومات حسب مستوى الخطورة",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "score": 72,
                "grade": "B",
                "color": "#F59E0B",
                "label": "جيد — يوجد مجال للتحسين",
                "breakdown": {
                    "high": {"count": 1, "deduction": -15},
                    "medium": {"count": 2, "deduction": -16},
                    "low": {"count": 0, "deduction": 0},
                    "informational": {"count": 3, "deduction": -3},
                },
            }
        }


# ─── التقرير الكامل ───

class FullReport(BaseModel):
    """التقرير الأمني الكامل — يجمع نتائج ZAP + تحليل AI + مؤشر الأمان."""
    scan_id: str = Field(..., description="المُعرّف الفريد للفحص")
    target_url: str = Field(..., description="الرابط المُفحص")
    scan_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="تاريخ ووقت الفحص",
    )
    security_score: SecurityScore = Field(..., description="مؤشر الأمان المحسوب")
    total_vulnerabilities: int = Field(
        default=0,
        description="العدد الإجمالي للثغرات المكتشفة",
    )
    false_positives_count: int = Field(
        default=0,
        description="عدد الإنذارات الخاطئة المُستبعدة",
    )
    vulnerabilities: List[Vulnerability] = Field(
        default_factory=list,
        description="قائمة الثغرات الخام من ZAP",
    )
    ai_analysis: List[AIVulnerabilityAnalysis] = Field(
        default_factory=list,
        description="تحليل الذكاء الاصطناعي لكل ثغرة",
    )
    summary: str = Field(
        default="",
        description="ملخص عام للتقرير من الذكاء الاصطناعي",
    )


class ReportListItem(BaseModel):
    """عنصر مختصر من قائمة التقارير — للعرض في الجدول."""
    scan_id: str
    target_url: str
    scan_date: datetime
    score: int
    grade: str
    total_vulnerabilities: int
    status: str
