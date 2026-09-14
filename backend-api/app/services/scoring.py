"""
WebGuard AI — Security Score Calculator
=========================================
خوارزمية حساب مؤشر الأمان (Security Score) — متطلب الدكتور المشرف.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
آلية الحساب:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • النقطة الابتدائية: 100 (آمن تماماً)
  • خصم لكل ثغرة عالية الخطورة (High): -15 نقطة
  • خصم لكل ثغرة متوسطة (Medium): -8 نقاط
  • خصم لكل ثغرة منخفضة (Low): -3 نقاط
  • خصم لكل ثغرة معلوماتية (Informational): -1 نقطة
  • الحد الأدنى: 0 (الأقصى خطورة)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

التصنيف:
  A+  (95-100): ممتاز — الموقع آمن جداً
  A   (85-94):  جيد جداً — ثغرات طفيفة
  B   (70-84):  جيد — يحتاج بعض التحسينات
  C   (50-69):  متوسط — ثغرات تحتاج معالجة
  D   (30-49):  ضعيف — ثغرات خطيرة
  F   (0-29):   خطير — يتطلب إصلاحاً فورياً
"""

from app.models.report import SecurityScore, SecurityGrade


# ─── أوزان الخصم لكل مستوى خطورة ───
RISK_WEIGHTS = {
    "High": 15,
    "Medium": 8,
    "Low": 3,
    "Informational": 1,
}

# ─── جدول التصنيف (Grade) ───
GRADE_THRESHOLDS = [
    (95, SecurityGrade.A_PLUS, "#10B981", "ممتاز — الموقع آمن جداً"),
    (85, SecurityGrade.A, "#22C55E", "جيد جداً — ثغرات طفيفة فقط"),
    (70, SecurityGrade.B, "#F59E0B", "جيد — يحتاج بعض التحسينات"),
    (50, SecurityGrade.C, "#F97316", "متوسط — ثغرات تحتاج معالجة"),
    (30, SecurityGrade.D, "#EF4444", "ضعيف — ثغرات خطيرة موجودة"),
    (0, SecurityGrade.F, "#DC2626", "خطير — يتطلب إصلاحاً فورياً"),
]


def calculate_security_score(vulnerabilities: list) -> SecurityScore:
    """
    يحسب مؤشر الأمان بناءً على قائمة الثغرات المكتشفة.
    
    Args:
        vulnerabilities: قائمة الثغرات — كل ثغرة يجب أن تحتوي على مفتاح 'risk'
    
    Returns:
        SecurityScore: كائن يحتوي على الدرجة والتقدير واللون والتفصيل
    """
    # ─── 1. عدّ الثغرات حسب المستوى ───
    counts = {"High": 0, "Medium": 0, "Low": 0, "Informational": 0}
    for vuln in vulnerabilities:
        risk = vuln.get("risk", "Informational")
        if risk in counts:
            counts[risk] += 1

    # ─── 2. حساب الخصومات ───
    breakdown = {}
    total_deduction = 0

    for risk_level, count in counts.items():
        weight = RISK_WEIGHTS.get(risk_level, 0)
        deduction = count * weight
        total_deduction += deduction
        breakdown[risk_level.lower()] = {
            "count": count,
            "weight": weight,
            "deduction": -deduction,
        }

    # ─── 3. حساب الدرجة النهائية (لا تقل عن 0) ───
    score = max(0, 100 - total_deduction)

    # ─── 4. تحديد التقدير واللون ───
    grade = SecurityGrade.F
    color = "#DC2626"
    label = "خطير — يتطلب إصلاحاً فورياً"

    for threshold, g, c, l in GRADE_THRESHOLDS:
        if score >= threshold:
            grade = g
            color = c
            label = l
            break

    return SecurityScore(
        score=score,
        grade=grade,
        color=color,
        label=label,
        breakdown=breakdown,
    )
