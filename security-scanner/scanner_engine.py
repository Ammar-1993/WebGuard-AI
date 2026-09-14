"""
WebGuard AI — Security Scanner Engine (OWASP ZAP Wrapper)
============================================================
خدمة محرك الفحص الأمني — تعمل كجسر بين الخادم المركزي ومحرك OWASP ZAP.

المسؤولية:
  - استقبال رابط الموقع المراد فحصه من الخادم المركزي
  - التحقق من صلاحية الرابط
  - تشغيل Spider (اكتشاف الصفحات)
  - تشغيل Active Scan (فحص الثغرات)
  - جمع النتائج وإعادتها بصيغة JSON منظمة

ملاحظة مهمة (متطلب الدكتور المشرف):
  الذكاء الاصطناعي لا يُستخدم هنا إطلاقاً.
  هذه الخدمة تعتمد فقط على محرك OWASP ZAP لاكتشاف الثغرات.

التشغيل:
  uvicorn scanner_engine:app --host 0.0.0.0 --port 8012
"""

import os
import time

import requests
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, HttpUrl
from zapv2 import ZAPv2

# ═══════════════════════════════════════════
#  إعداد التطبيق
# ═══════════════════════════════════════════

app = FastAPI(
    title="WebGuard AI — Security Scanner",
    version="1.0.0",
    description="خدمة الفحص الأمني — OWASP ZAP Wrapper",
)

# ─── قراءة عنوان ZAP من متغيرات البيئة ───
ZAP_URL = os.getenv("ZAP_URL", "http://owasp-zap:8092")

# ─── إنشاء عميل ZAP ───
zap = ZAPv2(
    apikey="",  # مفتاح API معطّل في docker-compose (api.disablekey=true)
    proxies={
        "http": ZAP_URL,
        "https": ZAP_URL,
    },
)


# ═══════════════════════════════════════════
#  نماذج البيانات
# ═══════════════════════════════════════════

class ScanRequest(BaseModel):
    """طلب فحص أمني — يُرسله الخادم المركزي."""
    target_url: HttpUrl

    class Config:
        json_schema_extra = {
            "example": {"target_url": "https://example.com"}
        }


# ═══════════════════════════════════════════
#  دوال مساعدة
# ═══════════════════════════════════════════

def _validate_url_reachable(url: str) -> bool:
    """يتحقق من أن الرابط المُدخل قابل للوصول (Sanity Check)."""
    try:
        resp = requests.get(url, timeout=15, allow_redirects=True)
        return resp.status_code < 500
    except requests.RequestException:
        return False


def _wait_for_spider(target: str, max_wait: int = 120) -> int:
    """
    يُشغّل Spider لاكتشاف صفحات الموقع وينتظر اكتماله.
    
    Returns:
        عدد الروابط المكتشفة
    """
    print(f"🕷️ بدء Spider على: {target}")
    scan_id = zap.spider.scan(target)
    elapsed = 0

    while int(zap.spider.status(scan_id)) < 100:
        time.sleep(3)
        elapsed += 3
        progress = zap.spider.status(scan_id)
        print(f"   Spider progress: {progress}%")
        if elapsed > max_wait:
            print("⚠️ تجاوز الوقت المحدد لـ Spider")
            zap.spider.stop(scan_id)
            break

    results = zap.spider.results(scan_id)
    print(f"✅ Spider اكتمل — تم اكتشاف {len(results)} رابط")
    return len(results)


def _wait_for_active_scan(target: str, max_wait: int = 300) -> None:
    """
    يُشغّل Active Scan (فحص الثغرات الفعلي) وينتظر اكتماله.
    هذا هو الجزء الذي يكتشف فيه ZAP الثغرات الأمنية.
    """
    print(f"🔍 بدء Active Scan على: {target}")
    scan_id = zap.ascan.scan(target)
    elapsed = 0

    while int(zap.ascan.status(scan_id)) < 100:
        time.sleep(5)
        elapsed += 5
        progress = zap.ascan.status(scan_id)
        print(f"   Active Scan progress: {progress}%")
        if elapsed > max_wait:
            print("⚠️ تجاوز الوقت المحدد لـ Active Scan")
            zap.ascan.stop(scan_id)
            break

    print("✅ Active Scan اكتمل")


# ═══════════════════════════════════════════
#  مسارات API
# ═══════════════════════════════════════════

@app.post(
    "/api/scan",
    summary="بدء فحص أمني",
    description="يستقبل الرابط → يشغّل ZAP Spider → Active Scan → يُعيد الثغرات المكتشفة.",
)
async def run_scan(scan_request: ScanRequest):
    """
    يُنفّذ الفحص الأمني الكامل:
    1. التحقق من صلاحية الرابط
    2. فتح الرابط في ZAP
    3. تشغيل Spider (اكتشاف الصفحات)
    4. تشغيل Active Scan (فحص الثغرات)
    5. جمع وإرجاع النتائج
    """
    target = str(scan_request.target_url)

    # ─── 1. التحقق من صلاحية الرابط ───
    if not _validate_url_reachable(target):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"الرابط غير قابل للوصول: {target}",
        )

    try:
        # ─── 2. فتح الرابط في ZAP ───
        print(f"🌐 فتح الرابط في ZAP: {target}")
        zap.urlopen(target)
        time.sleep(2)  # انتظار قصير ليُعالج ZAP الرابط

        # ─── 3. تشغيل Spider ───
        urls_found = _wait_for_spider(target)

        # ─── 4. تشغيل Active Scan ───
        _wait_for_active_scan(target)

        # ─── 5. جمع النتائج ───
        alerts = zap.core.alerts(baseurl=target, start=0, count=500)

        # ─── تنظيف النتائج ───
        cleaned_alerts = []
        for alert in alerts:
            cleaned_alerts.append({
                "name": alert.get("name", "Unknown"),
                "risk": alert.get("risk", "Informational"),
                "confidence": alert.get("confidence", "Medium"),
                "description": alert.get("description", ""),
                "solution": alert.get("solution", ""),
                "url": alert.get("url", ""),
                "cweid": alert.get("cweid", ""),
                "wascid": alert.get("wascid", ""),
                "evidence": alert.get("evidence", ""),
                "reference": alert.get("reference", ""),
            })

        print(f"📊 النتائج: {len(cleaned_alerts)} تنبيه أمني مكتشف")

        return {
            "status": "completed",
            "target_url": target,
            "urls_discovered": urls_found,
            "total_alerts": len(cleaned_alerts),
            "alerts": cleaned_alerts,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ أثناء الفحص: {str(e)}. تأكد من أن محرك ZAP يعمل.",
        )


@app.get(
    "/health",
    summary="فحص صحة الخدمة",
)
async def health():
    """يتحقق من جاهزية خدمة الفحص واتصالها بـ ZAP."""
    try:
        version = zap.core.version
        return {
            "status": "ok",
            "service": "Security Scanner",
            "zap_version": version,
            "zap_url": ZAP_URL,
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "Security Scanner",
            "error": f"ZAP غير متاح: {str(e)}",
            "zap_url": ZAP_URL,
        }


@app.get("/", summary="الصفحة الرئيسية")
async def root():
    return {
        "service": "WebGuard AI — Security Scanner",
        "status": "running",
        "description": "خدمة محرك الفحص الأمني (OWASP ZAP Wrapper)",
    }
