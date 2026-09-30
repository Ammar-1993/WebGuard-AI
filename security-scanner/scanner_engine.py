"""
WebGuard AI — Security Scanner Engine (OWASP ZAP Wrapper)
============================================================
خدمة محرك الفحص الأمني — تعمل كجسر بين الخادم المركزي ومحرك OWASP ZAP.

المسؤولية:
  - استقبال رابط الموقع المراد فحصه من الخادم المركزي
  - التحقق من صلاحية الرابط (وأمانه — انظر SSRF PROTECTION أدناه)
  - تشغيل Spider (اكتشاف الصفحات)
  - تشغيل Active Scan (فحص الثغرات)
  - جمع النتائج وإعادتها بصيغة JSON منظمة

ملاحظة مهمة (متطلب الدكتور المشرف):
  الذكاء الاصطناعي لا يُستخدم هنا إطلاقاً.
  هذه الخدمة تعتمد فقط على محرك OWASP ZAP لاكتشاف الثغرات.

═══════════════════════════════════════════════════════════════
SSRF PROTECTION (Security Review — البند 2.1)
═══════════════════════════════════════════════════════════════
هذه الخدمة أداة DAST — استخدامها المشروع الأساسي غالبًا يتضمن فحص أهداف
داخل شبكات خاصة (مثل OWASP Juice Shop على localhost، أو تطبيقات داخل
شبكة الشركة). لذلك لا يصح حظر كل عناوين IP الخاصة (RFC1918) بشكل مطلق —
هذا يكسر الاستخدام الأساسي الموثّق في README نفسه.

الحل هنا مبني على 3 طبقات متدرجة:

  1. حظر دائم (غير قابل للتعطيل) لأسماء خدمات WebGuard AI الداخلية
     نفسها (mongodb, backend-api, ai-analyzer, security-scanner,
     owasp-zap) — لا يوجد أي سيناريو DAST مشروع يبرر توجيه فحص أمني
     نحو البنية التحتية الخاصة بالأداة نفسها.

  2. حظر دائم لعنوان Link-Local (169.254.0.0/16) — يشمل نقطة
     الـ Cloud Metadata (مثل 169.254.169.254 في AWS/GCP/Azure) التي
     لا يوجد لها أي استخدام DAST مشروع مطلقًا.

  3. حظر افتراضي (قابل للتفعيل/التعطيل عبر متغير بيئة) لعناوين
     Private/Loopback العامة — مفعّل بشكل افتراضي (Secure by Default)،
     ويمكن السماح به فعليًا في بيئات pentesting داخلية موثوقة عبر:
       SCANNER_ALLOW_PRIVATE_NETWORKS=true
     أو بإضافة استثناء محدد عبر:
       SCANNER_ALLOWED_HOSTS=frontend,my-internal-app.local

  قيد معروف (Known Limitation — DNS Rebinding):
  يتم التحقق بحل اسم الاستضافة (DNS resolution) لحظة الفحص فقط. مهاجم
  متقدّم يتحكم بخادم DNS يمكنه نظريًا تغيير الاستجابة بين لحظة التحقق
  ولحظة اتصال ZAP الفعلي (Time-of-Check-to-Time-of-Use). الحل الأكمل
  لهذا يكون على مستوى الشبكة (عزل شبكي/firewall egress rules على حاوية
  owasp-zap نفسها) لا على مستوى كود التطبيق فقط — يُنصح به كطبقة إضافية
  في بيئات إنتاج حساسة.

التشغيل:
  uvicorn scanner_engine:app --host 0.0.0.0 --port 8012
"""

import ipaddress
import os
import socket
import time
from urllib.parse import urlparse

import requests
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, HttpUrl
from zapv2 import ZAPv2

# ═══════════════════════════════════════════
#  إعداد التطبيق
# ═══════════════════════════════════════════

app = FastAPI(
    title="WebGuard AI — Security Scanner",
    version="1.1.0",
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
#  إعدادات حماية SSRF
# ═══════════════════════════════════════════

# ─── طبقة 1: أسماء خدمات WebGuard AI الداخلية — حظر دائم غير قابل للتعطيل ───
ALWAYS_BLOCKED_HOSTNAMES = {
    "mongodb",
    "backend-api",
    "ai-analyzer",
    "security-scanner",
    "owasp-zap",
}

# ─── طبقة 3: هل نسمح بفحص عناوين Private/Loopback بشكل عام؟ ───
# القيمة الافتراضية False = آمن افتراضيًا. يُفعَّل فقط في بيئات pentesting
# داخلية موثوقة تعرف أنها تفحص أهدافًا داخل شبكتها عمدًا.
ALLOW_PRIVATE_NETWORKS = os.getenv("SCANNER_ALLOW_PRIVATE_NETWORKS", "false").lower() == "true"

# ─── استثناءات محددة لأسماء استضافة مسموح بفحصها حتى لو كانت private/loopback ───
# القيمة الافتراضية "frontend" لأنه الهدف التجريبي الموثّق فعليًا في بيانات
# المشروع نفسه (سجلات فحص سابقة على frontend:3030 داخل الشبكة الداخلية).
_default_allowed = "frontend"
SCANNER_ALLOWED_HOSTS = {
    h.strip().lower()
    for h in os.getenv("SCANNER_ALLOWED_HOSTS", _default_allowed).split(",")
    if h.strip()
}


class SSRFValidationError(Exception):
    """يُرفع عند رفض هدف الفحص لأسباب أمنية (SSRF)."""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def _is_safe_target(url: str) -> None:
    """
    يتحقق من أن رابط الهدف لا يشير إلى بنية WebGuard AI الداخلية أو إلى
    عنوان محظور دائمًا (مثل Cloud Metadata). يرفع SSRFValidationError عند الرفض.

    ─── ملاحظة DNS ───
    حاوية الـ Scanner لا تملك وصولاً مباشراً للـ DNS العام للإنترنت (الحاوية تعمل
    داخل شبكة Docker الداخلية فقط). لذلك:
    - إذا أمكن حل الـ hostname → نتحقق من نطاق الـ IP.
    - إذا فشل حل الـ hostname (DNS error):
        * الخدمات الداخلية محظورة بالفعل في Layer 1 (بالاسم).
        * الـ hostname الخارجي غير القابل للحل لا يمكن أن يكون خدمة داخلية
          (الخدمات الداخلية تُحلّ دائماً داخل Docker) → نسمح به ونترك ZAP
          يحاول الوصول (ZAP يملك DNS access كافٍ).
    """
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()

    if not hostname:
        raise SSRFValidationError("Could not parse a hostname from the target URL")

    # ─── طبقة 1: أسماء خدمات WebGuard AI الداخلية — حظر دائم بالاسم ───
    # هذا الحظر يعمل بغض النظر عن DNS — الأسماء واضحة ومعروفة.
    if hostname in ALWAYS_BLOCKED_HOSTNAMES:
        raise SSRFValidationError(
            f"Target hostname '{hostname}' is a WebGuard AI internal service — "
            "scanning internal infrastructure is never permitted."
        )

    # ─── إذا كان الـ hostname عنوان IP مباشر → نتحقق منه فوراً ───
    try:
        ip_obj_direct = ipaddress.ip_address(hostname)
        # الـ hostname هو IP مباشر — نطبق فحص النطاق مباشرة
        _check_ip_range(ip_obj_direct, hostname)
        return  # اجتاز الفحص
    except ValueError:
        pass  # ليس IP مباشراً — متابعة بحل الـ DNS

    # ─── محاولة حل اسم الاستضافة إلى عنوان IP ───
    try:
        resolved_ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(resolved_ip)
        _check_ip_range(ip_obj, hostname, resolved_ip)
    except socket.gaierror:
        # DNS resolution فشل — هذا يحدث عندما تحاول الحاوية حل أسماء إنترنت عامة.
        # الخدمات الداخلية (Docker) تُحلّ دائماً بنجاح داخل الشبكة — لذا أي hostname
        # فشل حله هو على الأغلب هدف إنترنت خارجي مشروع.
        # ZAP لديه وصول أوسع للشبكة ويستطيع الوصول لمثل هذه الأهداف.
        print(f"⚠️  DNS resolution for '{hostname}' failed in scanner container "
              f"(expected for public internet targets) — deferring to ZAP.")
        return  # السماح بالمتابعة — ZAP سيحاول الاتصال الفعلي


def _check_ip_range(ip_obj: ipaddress.IPv4Address, hostname: str, resolved_ip: str = "") -> None:
    """
    يتحقق من نطاق عنوان IP — مُستدعى من _is_safe_target.
    يرفع SSRFValidationError إذا كان العنوان في نطاق محظور.
    """
    display = resolved_ip or str(ip_obj)

    # ─── طبقة 2: Link-Local (يشمل Cloud Metadata) — حظر دائم غير قابل للتعطيل ───
    if ip_obj.is_link_local:
        raise SSRFValidationError(
            f"Target resolves to a link-local address ({display}) — "
            "this range includes cloud metadata endpoints and is always blocked."
        )

    # ─── طبقة 3: Private/Loopback/Reserved — حظر افتراضي، قابل للاستثناء ───
    is_sensitive_range = ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved
    if is_sensitive_range and not ALLOW_PRIVATE_NETWORKS and hostname not in SCANNER_ALLOWED_HOSTS:
        raise SSRFValidationError(
            f"Target '{hostname}' resolves to a private/internal address ({display}). "
            "Scanning private networks is disabled by default. If this is an authorized "
            "internal pentesting target, add it to SCANNER_ALLOWED_HOSTS or set "
            "SCANNER_ALLOW_PRIVATE_NETWORKS=true."
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
    print(f"🕷️ Starting Spider on: {target}")
    scan_id = zap.spider.scan(target)
    elapsed = 0

    while int(zap.spider.status(scan_id)) < 100:
        time.sleep(3)
        elapsed += 3
        progress = zap.spider.status(scan_id)
        print(f"   Spider progress: {progress}%")
        if elapsed > max_wait:
            print("⚠️ Spider timeout exceeded")
            zap.spider.stop(scan_id)
            break

    results = zap.spider.results(scan_id)
    print(f"✅ Spider completed — discovered {len(results)} URLs")
    return len(results)


def _wait_for_active_scan(target: str, max_wait: int = 300) -> None:
    """
    يُشغّل Active Scan (فحص الثغرات الفعلي) وينتظر اكتماله.
    هذا هو الجزء الذي يكتشف فيه ZAP الثغرات الأمنية.
    """
    print(f"🔍 Starting Active Scan on: {target}")
    scan_id = zap.ascan.scan(target)
    elapsed = 0

    while int(zap.ascan.status(scan_id)) < 100:
        time.sleep(5)
        elapsed += 5
        progress = zap.ascan.status(scan_id)
        print(f"   Active Scan progress: {progress}%")
        if elapsed > max_wait:
            print("⚠️ Active Scan timeout exceeded")
            zap.ascan.stop(scan_id)
            break

    print("✅ Active Scan completed")


# ═══════════════════════════════════════════
#  مسارات API
# ═══════════════════════════════════════════

@app.post(
    "/api/scan",
    summary="بدء فحص أمني",
    description="يستقبل الرابط → يتحقق من أمانه (SSRF) → يشغّل ZAP Spider → Active Scan → يُعيد الثغرات المكتشفة.",
)
async def run_scan(scan_request: ScanRequest):
    """
    يُنفّذ الفحص الأمني الكامل:
    1. التحقق من أمان الهدف (SSRF Protection)
    2. التحقق من صلاحية الرابط
    3. فتح الرابط في ZAP
    4. تشغيل Spider (اكتشاف الصفحات)
    5. تشغيل Active Scan (فحص الثغرات)
    6. جمع وإرجاع النتائج
    """
    target = str(scan_request.target_url)

    # ─── 1. التحقق من أمان الهدف (SSRF) — قبل أي اتصال فعلي بالرابط ───
    try:
        _is_safe_target(target)
    except SSRFValidationError as e:
        print(f"🚫 SSRF check rejected target: {target} — {e.reason}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Target rejected for security reasons: {e.reason}",
        )

    # ─── 2. التحقق من صلاحية الرابط ───
    if not _validate_url_reachable(target):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"URL is unreachable: {target}",
        )

    try:
        # ─── 3. فتح الرابط في ZAP ───
        print(f"🌐 Opening URL in ZAP: {target}")
        zap.urlopen(target)
        time.sleep(2)  # انتظار قصير ليُعالج ZAP الرابط

        # ─── 4. تشغيل Spider ───
        urls_found = _wait_for_spider(target)

        # ─── 5. تشغيل Active Scan ───
        _wait_for_active_scan(target)

        # ─── 6. جمع النتائج ───
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

        print(f"📊 Results: {len(cleaned_alerts)} security alerts discovered")

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
            detail=f"Error during scan: {str(e)}. Ensure ZAP engine is running.",
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
            "ssrf_protection": {
                "allow_private_networks": ALLOW_PRIVATE_NETWORKS,
                "allowed_hosts": sorted(SCANNER_ALLOWED_HOSTS),
            },
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "Security Scanner",
            "error": f"ZAP is unavailable: {str(e)}",
            "zap_url": ZAP_URL,
        }


@app.get("/", summary="الصفحة الرئيسية")
async def root():
    return {
        "service": "WebGuard AI — Security Scanner",
        "status": "running",
        "description": "Security Scanner Engine Service (OWASP ZAP Wrapper)",
    }