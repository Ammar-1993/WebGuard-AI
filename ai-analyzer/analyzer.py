"""
WebGuard AI — AI Analyzer Service (LangChain + OpenAI)
========================================================
خدمة الذكاء الاصطناعي المستقلة — تحلل نتائج ZAP الخام وتقدم:
  1. وصف مبسّط لكل ثغرة (بلغة المطوّر)
  2. تحديد الإنذارات الخاطئة (False Positives) مع التبرير
  3. كود إصلاح جاهز للتطبيق

ملاحظة مهمة (متطلب الدكتور المشرف):
  هذه الخدمة لا تكتشف الثغرات — فقط تُحلل ما اكتشفه OWASP ZAP.

التشغيل:
  uvicorn analyzer:app --host 0.0.0.0 --port 8011
"""

import json
import os
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

# ═══════════════════════════════════════════
#  إعداد التطبيق
# ═══════════════════════════════════════════

app = FastAPI(
    title="WebGuard AI — AI Analyzer",
    version="1.0.0",
    description="خدمة تحليل الثغرات بالذكاء الاصطناعي — LangChain + OpenAI",
)

# ─── قراءة مفتاح OpenAI من متغيرات البيئة ───
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ─── قراءة System Prompt من الملف ───
PROMPT_PATH = Path(__file__).parent / "prompts" / "system_prompt.txt"
SYSTEM_PROMPT = ""
if PROMPT_PATH.exists():
    SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")
else:
    SYSTEM_PROMPT = "You are a cybersecurity expert. Analyze the vulnerabilities and provide remediation advice in JSON format."


# ═══════════════════════════════════════════
#  نماذج البيانات
# ═══════════════════════════════════════════

class AnalyzeRequest(BaseModel):
    """طلب تحليل — يحتوي على قائمة الثغرات الخام من ZAP."""
    alerts: List[dict]

    class Config:
        json_schema_extra = {
            "example": {
                "alerts": [
                    {
                        "name": "Cross-Site Scripting (XSS)",
                        "risk": "High",
                        "description": "Cross-site scripting vulnerability found",
                        "url": "https://example.com/search?q=test",
                        "solution": "Validate and encode user input",
                    }
                ]
            }
        }


# ═══════════════════════════════════════════
#  دالة التحليل بالذكاء الاصطناعي
# ═══════════════════════════════════════════

async def _analyze_with_ai(alerts: List[dict]) -> dict:
    """
    يُرسل الثغرات لـ OpenAI عبر LangChain ويُعيد التحليل.
    
    Args:
        alerts: قائمة الثغرات الخام من ZAP
    
    Returns:
        dict: التحليل المنظّم (analysis + summary)
    """
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="مفتاح OpenAI API غير مُعرّف. أضفه في ملف .env",
        )

    # ─── إنشاء نموذج LangChain ───
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,  # حرارة منخفضة لنتائج دقيقة ومتسقة
        api_key=OPENAI_API_KEY,
        max_tokens=4000,
    )

    # ─── تحضير البيانات للإرسال ───
    # نُرسل فقط الحقول المهمة لتقليل عدد الـ tokens
    simplified_alerts = []
    for alert in alerts:
        simplified_alerts.append({
            "name": alert.get("name", "Unknown"),
            "risk": alert.get("risk", "Informational"),
            "confidence": alert.get("confidence", "Medium"),
            "description": alert.get("description", "")[:500],
            "solution": alert.get("solution", "")[:300],
            "url": alert.get("url", ""),
            "cweid": alert.get("cweid", ""),
            "evidence": alert.get("evidence", "")[:200],
        })

    user_message = (
        "Analyze the following vulnerability alerts discovered by OWASP ZAP.\n"
        "Return your analysis as valid JSON only.\n\n"
        f"ALERTS:\n{json.dumps(simplified_alerts, indent=2)}"
    )

    # ─── استدعاء OpenAI عبر LangChain ───
    try:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ]
        response = await llm.ainvoke(messages)
        response_text = response.content.strip()

        # ─── تنظيف الاستجابة (إزالة markdown إن وُجد) ───
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        # ─── تحويل لـ JSON ───
        result = json.loads(response_text)
        return result

    except json.JSONDecodeError as e:
        print(f"⚠️ فشل تحليل استجابة AI كـ JSON: {e}")
        print(f"   الاستجابة الخام: {response_text[:500]}")
        # ─── إرجاع تحليل افتراضي في حالة فشل التحليل ───
        return _generate_fallback_analysis(alerts)

    except Exception as e:
        print(f"❌ خطأ في استدعاء OpenAI: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"فشل تحليل الذكاء الاصطناعي: {str(e)}",
        )


def _generate_fallback_analysis(alerts: List[dict]) -> dict:
    """
    يولّد تحليلاً افتراضياً إذا فشل استدعاء OpenAI.
    يضمن عدم انهيار النظام حتى بدون AI.
    """
    analysis = []
    for alert in alerts:
        analysis.append({
            "original_name": alert.get("name", "Unknown"),
            "risk": alert.get("risk", "Informational"),
            "is_false_positive": False,
            "false_positive_reason": "",
            "simplified_description": alert.get("description", "ثغرة أمنية تم اكتشافها بواسطة محرك ZAP.")[:200],
            "impact": "يُرجى مراجعة التفاصيل التقنية لتقييم التأثير.",
            "remediation_steps": [alert.get("solution", "راجع الوثائق الأمنية ذات الصلة.")],
            "remediation_code": "",
            "code_language": "",
        })

    return {
        "analysis": analysis,
        "summary": f"تم اكتشاف {len(alerts)} تنبيه أمني. يُرجى مراجعة كل ثغرة على حدة.",
    }


# ═══════════════════════════════════════════
#  مسارات API
# ═══════════════════════════════════════════

@app.post(
    "/api/analyze",
    summary="تحليل الثغرات بالذكاء الاصطناعي",
    description="يستقبل نتائج ZAP الخام ويُعيد تحليلاً مبسّطاً مع أكواد إصلاح.",
)
async def analyze_vulnerabilities(request: AnalyzeRequest):
    """
    يُحلل الثغرات المكتشفة بواسطة ZAP ويُعيد:
    - وصف مبسّط لكل ثغرة
    - تحديد الإنذارات الخاطئة
    - أكواد إصلاح جاهزة
    - ملخص عام
    """
    if not request.alerts:
        return {
            "analysis": [],
            "summary": "لم يتم العثور على أي ثغرات أمنية. الموقع يبدو آمناً! ✅",
        }

    print(f"🧠 بدء تحليل {len(request.alerts)} تنبيه أمني بالذكاء الاصطناعي...")
    result = await _analyze_with_ai(request.alerts)
    print(f"✅ اكتمل التحليل — {len(result.get('analysis', []))} ثغرة مُحلّلة")

    return result


@app.get(
    "/health",
    summary="فحص صحة الخدمة",
)
async def health():
    """يتحقق من جاهزية خدمة الذكاء الاصطناعي."""
    api_key_status = "configured" if OPENAI_API_KEY else "missing"
    return {
        "status": "ok" if OPENAI_API_KEY else "degraded",
        "service": "AI Analyzer",
        "openai_api_key": api_key_status,
        "model": "gpt-4o-mini",
    }


@app.get("/", summary="الصفحة الرئيسية")
async def root():
    return {
        "service": "WebGuard AI — AI Analyzer",
        "status": "running",
        "description": "خدمة تحليل الثغرات بالذكاء الاصطناعي (LangChain + OpenAI)",
    }
