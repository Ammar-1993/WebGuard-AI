"""
WebGuard AI — Scanner Client Service
======================================
عميل HTTP غير متزامن للتواصل مع خدمة Security Scanner.
يُرسل رابط الموقع المُراد فحصه ويستقبل نتائج ZAP الخام.
"""

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings


# مهلة طويلة لأن فحص ZAP قد يستغرق وقتاً
SCANNER_TIMEOUT = 600.0  # 10 دقائق


async def start_scan(target_url: str) -> dict:
    """
    يُرسل طلب فحص أمني لخدمة Security Scanner.
    
    Args:
        target_url: رابط الموقع المراد فحصه
    
    Returns:
        dict: نتائج الفحص الخام من ZAP (قائمة الثغرات)
    
    Raises:
        HTTPException 503: إذا كانت خدمة الفحص غير متاحة
        HTTPException 500: إذا حدث خطأ أثناء الفحص
    """
    settings = get_settings()
    scanner_url = f"{settings.SCANNER_SERVICE_URL}/api/scan"

    try:
        async with httpx.AsyncClient(timeout=SCANNER_TIMEOUT) as client:
            response = await client.post(
                scanner_url,
                json={"target_url": str(target_url)},
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Security scan failed: {response.text}",
                )

    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Security Scanner service is currently unavailable. Ensure the container is running.",
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Security scan timed out. The target site might be too large.",
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error connecting to Scanner service: {str(e)}",
        )


async def check_scanner_health() -> bool:
    """يتحقق من جاهزية خدمة Security Scanner."""
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.SCANNER_SERVICE_URL}/health")
            return response.status_code == 200
    except Exception:
        return False
