"""
WebGuard AI — Redis Connection & Distributed Lock Manager
==========================================================
يدير الاتصال بخدمة Redis ويوفر آلية القفل الموزع (Distributed Lock)
لمنع تكرار فحص نفس الرابط في وقت واحد عبر نسخ الخادم المختلفة.
"""

import logging
from typing import Optional

from app.core.config import get_settings

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

logger = logging.getLogger("webguard-redis")

redis_client: Optional["aioredis.Redis"] = None

# مدة بقاء القفل كحد أقصى (15 دقيقة) لمنع بقاء القفل معلقاً في حال تعطل الخادم
DEFAULT_LOCK_TTL = 900


async def get_redis():
    """
    يُرجع عميل Redis غير متزامن.
    في حال فشل الاتصال، يُرجع None ليعمل النظام بدون كاش دون أن ينهار (Graceful Degradation).
    """
    global redis_client
    if aioredis is None:
        return None
    settings = get_settings()
    if not settings.REDIS_URL:
        return None
    if redis_client is None:
        try:
            redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=3.0,
                socket_connect_timeout=3.0,
            )
        except Exception as e:
            logger.warning("Could not initialize Redis client: %s", e)
            redis_client = None
    return redis_client


async def connect_redis():
    """التحقق من الاتصال بـ Redis عند بدء تشغيل الخادم."""
    try:
        r = await get_redis()
        if r:
            await r.ping()
            print("✅ Connected to Redis successfully")
    except Exception as e:
        print(f"⚠️ Redis connection warning on startup: {e} (Continuing without distributed locks)")


async def close_redis():
    """إغلاق الاتصال بـ Redis عند إيقاف الخادم."""
    global redis_client
    if redis_client:
        try:
            await redis_client.close()
            print("🔌 Redis connection closed")
        except Exception:
            pass


def _normalize_lock_url(target_url: str) -> str:
    """
    توحيد صيغة الرابط (URL Normalization) لضمان دقة القفل:
    - تحويل الأحرف إلى lowercase
    - إزالة الـ trailing slash
    - إزالة الفراغات الزائدة
    """
    url = str(target_url).strip().lower()
    return url.rstrip("/")


def get_scan_lock_key(target_url: str) -> str:
    """توليد مفتاح القفل في Redis لرابط محدد."""
    norm = _normalize_lock_url(target_url)
    return f"lock:scan:{norm}"


async def acquire_scan_lock(target_url: str, scan_id: str, ttl: int = DEFAULT_LOCK_TTL) -> bool:
    """
    محاولة حيازة قفل موزع لفحص رابط محدد.
    يستخدم SET key value NX EX ttl كعملية ذرية (Atomic Operation).
    
    Args:
        target_url: رابط الموقع المستهدف
        scan_id: معرّف الفحص الذي يحوز القفل
        ttl: مدة انتهاء صلاحية القفل التلقائية بالثواني (افتراضياً 900 ثانية = 15 دقيقة)
        
    Returns:
        bool: True إذا تم حيازة القفل بنجاح، False إذا كان القفل محجوزاً بالفعل لعملية أخرى
    """
    r = await get_redis()
    if not r:
        logger.warning("Redis is unavailable — proceeding without acquiring distributed lock.")
        return True

    lock_key = get_scan_lock_key(target_url)
    try:
        acquired = await r.set(lock_key, scan_id, nx=True, ex=ttl)
        return bool(acquired)
    except Exception as e:
        logger.warning("Error acquiring scan lock for %s: %s", target_url, e)
        return True


async def release_scan_lock(target_url: str, scan_id: Optional[str] = None) -> bool:
    """
    تحرير القفل الموزع لرابط محدد بشكل آمن.
    إذا تم تمرير scan_id، يتم التحقق أولاً من أن القفل لا يزال مملوكاً لنفس الفحص لتفادي تحرير قفل لعملية أخرى.
    
    Args:
        target_url: رابط الموقع المستهدف
        scan_id: معرّف الفحص المالك للقفل (اختياري للتحقق الآمن)
        
    Returns:
        bool: True إذا تم تحرير القفل، False خلاف ذلك
    """
    r = await get_redis()
    if not r:
        return False

    lock_key = get_scan_lock_key(target_url)
    try:
        if scan_id:
            current_owner = await r.get(lock_key)
            if current_owner == scan_id:
                await r.delete(lock_key)
                logger.info("Successfully released scan lock for %s (scan_id=%s)", target_url, scan_id)
                return True
            else:
                logger.warning(
                    "Lock ownership mismatch for %s: current owner=%s, release caller=%s",
                    target_url, current_owner, scan_id,
                )
                return False
        else:
            await r.delete(lock_key)
            logger.info("Released scan lock for %s", target_url)
            return True
    except Exception as e:
        logger.warning("Error releasing scan lock for %s: %s", target_url, e)
        return False
