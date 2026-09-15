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
    name: str = Field(..., description="Vulnerability name")
    risk: RiskLevel = Field(..., description="Risk level")
    confidence: str = Field(default="Medium", description="Confidence level in the result")
    description: str = Field(default="", description="Technical description of the vulnerability")
    solution: str = Field(default="", description="Proposed solution by ZAP")
    url: str = Field(default="", description="URL affected by the vulnerability")
    cweid: str = Field(default="", description="International CWE ID")
    wascid: str = Field(default="", description="WASC ID")
    evidence: str = Field(default="", description="Evidence of the vulnerability")
    reference: str = Field(default="", description="Additional references")


# ─── تحليل الذكاء الاصطناعي لثغرة واحدة ───

class AIVulnerabilityAnalysis(BaseModel):
    """تحليل الذكاء الاصطناعي لثغرة أمنية واحدة."""
    original_name: str = Field(..., description="Original vulnerability name from ZAP")
    risk: RiskLevel = Field(..., description="Risk level")
    is_false_positive: bool = Field(
        default=False,
        description="Is it a false positive?",
    )
    false_positive_reason: str = Field(
        default="",
        description="Reason for being a false positive (if any)",
    )
    simplified_description: str = Field(
        ...,
        description="Simplified and understandable description of the vulnerability (developer language)",
    )
    impact: str = Field(
        default="",
        description="Potential impact of this vulnerability on the system",
    )
    remediation_steps: List[str] = Field(
        default_factory=list,
        description="Proposed remediation steps",
    )
    remediation_code: str = Field(
        default="",
        description="Ready-to-apply remediation code",
    )
    code_language: str = Field(
        default="",
        description="Language of remediation code (Python, JavaScript, PHP, etc.)",
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
        description="Numerical score (0-100)",
    )
    grade: SecurityGrade = Field(..., description="Letter grade (A+ to F)")
    color: str = Field(..., description="Score color (#hex)")
    label: str = Field(..., description="Brief text description of the status")
    breakdown: dict = Field(
        default_factory=dict,
        description="Breakdown of deductions by risk level",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "score": 72,
                "grade": "B",
                "color": "#F59E0B",
                "label": "Good — Room for improvement",
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
    scan_id: str = Field(..., description="Unique identifier for the scan")
    target_url: str = Field(..., description="Target URL")
    scan_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="Date and time of the scan",
    )
    security_score: SecurityScore = Field(..., description="Calculated security score")
    total_vulnerabilities: int = Field(
        default=0,
        description="Total number of discovered vulnerabilities",
    )
    false_positives_count: int = Field(
        default=0,
        description="Number of excluded false positives",
    )
    vulnerabilities: List[Vulnerability] = Field(
        default_factory=list,
        description="List of raw vulnerabilities from ZAP",
    )
    ai_analysis: List[AIVulnerabilityAnalysis] = Field(
        default_factory=list,
        description="AI analysis for each vulnerability",
    )
    summary: str = Field(
        default="",
        description="Overall report summary from AI",
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
