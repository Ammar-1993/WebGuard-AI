"""
WebGuard AI — AI Analyzer Client Service
==========================================
عميل HTTP غير متزامن للتواصل مع خدمة الذكاء الاصطناعي.
يُرسل نتائج ZAP الخام ويستقبل التحليل المُبسّط وأكواد الإصلاح.
"""

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings


# مهلة طويلة لأن تحليل AI قد يستغرق وقتاً (استدعاء OpenAI)
AI_TIMEOUT = 120.0  # دقيقتان


async def analyze_vulnerabilities(raw_alerts: list) -> dict:
    """
    يُرسل نتائج ZAP الخام لخدمة الذكاء الاصطناعي للتحليل.
    
    Args:
        raw_alerts: قائمة الثغرات الخام كما وردت من ZAP
    
    Returns:
        dict: التحليل المُبسّط يتضمن:
            - analysis: قائمة تحليل كل ثغرة
            - summary: ملخص عام
    
    Raises:
        HTTPException 503: إذا كانت خدمة الذكاء الاصطناعي غير متاحة
        HTTPException 500: إذا حدث خطأ أثناء التحليل
    """
    settings = get_settings()
    ai_url = f"{settings.AI_SERVICE_URL}/api/analyze"

    try:
        async with httpx.AsyncClient(timeout=AI_TIMEOUT) as client:
            response = await client.post(
                ai_url,
                json={"alerts": raw_alerts},
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"فشل تحليل الذكاء الاصطناعي: {response.text}",
                )

    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="خدمة الذكاء الاصطناعي غير متاحة حالياً. تأكد من تشغيل حاوية AI Analyzer.",
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="انتهت مهلة تحليل الذكاء الاصطناعي. حاول مرة أخرى.",
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في الاتصال بخدمة الذكاء الاصطناعي: {str(e)}",
        )


async def check_ai_health() -> bool:
    """يتحقق من جاهزية خدمة الذكاء الاصطناعي."""
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.AI_SERVICE_URL}/health")
            return response.status_code == 200
    except Exception:
        return False
