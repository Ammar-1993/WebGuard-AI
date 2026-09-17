# تقرير مراجعة أمنية — WebGuard AI

**المشروع:** WebGuard AI — DAST Security Scanning Platform
**النطاق:** `backend-api`, `security-scanner`, `ai-analyzer`, `frontend`, `docker-compose.yml`
**نوع المراجعة:** Static Code Review (مراجعة كود يدوية — بدون تشغيل فعلي للنظام)
**تاريخ المراجعة:** 2026-09-17

---

## 1. ملخص تنفيذي (Executive Summary)

المشروع مبني بمعمارية microservices نظيفة مع فصل واضح للمسؤوليات، ويطبّق ضوابط **BOLA/IDOR** بشكل حقيقي على مستوى الكود (وليس مجرد ادّعاء توثيقي). تم رصد **7 ملاحظات** خلال المراجعة، لا يوجد بينها ثغرة تتيح اختراقًا فوريًا في بيئة تطوير معزولة، لكن **ثغرتين (SSRF و JWT_SECRET الافتراضي) تشكلان خطرًا حقيقيًا** إذا انتقل المشروع لبيئة إنتاج أو تعرّض لشبكة غير موثوقة دون تعديل.

| # | الملاحظة | الخطورة | الحالة |
|---|---|:---:|---|
| 1 | SSRF عبر خدمة `security-scanner` نحو الشبكة الداخلية | 🔴 High | غير معالجة |
| 2 | قيمة افتراضية ضعيفة لـ `JWT_SECRET` | 🔴 High | غير معالجة |
| 3 | لا يوجد Rate Limiting على `/api/auth/login` | 🟠 Medium | غير معالجة |
| 4 | سياسة كلمة مرور ضعيفة (6 أحرف فقط) | 🟠 Medium | غير معالجة |
| 5 | بيانات اتصال قاعدة بيانات في `test_db.py` بجذر المشروع | 🟠 Medium | غير معالجة |
| 6 | عدم تقسيم (batching) تنبيهات ZAP الكبيرة قبل إرسالها للـ LLM | 🟡 Low | غير معالجة |
| 7 | ملفات مخرجات فحص (`reports_output.json`, `scans_output.json`) غير مستبعدة من الريبو | 🟡 Low | غير معالجة |

---

## 2. تفاصيل الثغرات

### 2.1 🔴 SSRF عبر خدمة الفحص (Server-Side Request Forgery)

**الموقع:** `security-scanner/scanner_engine.py` — دالة `run_scan()` و `_validate_url_reachable()`

**الوصف:**
الخدمة تقبل أي `target_url` من المستخدم المصادَق عليه وتمرره مباشرة إلى `zap.urlopen(target)` دون أي تحقق من كون الرابط يشير لعنوان داخلي. بما أن `owasp-zap` و `security-scanner` يعملان داخل شبكة Docker الداخلية `webguard_net`، يمكن لمستخدم خبيث توجيه الفحص نحو:
- خدمات داخلية أخرى مثل `http://mongodb:27017` أو `http://backend-api:8010`
- عناوين IP الخاصة (`127.0.0.1`, `169.254.169.254` — عنوان metadata في بيئات Cloud مثل AWS/GCP إن نُشر المشروع هناك)

**التأثير:** اكتشاف خدمات داخلية، احتمال تسريب معلومات حساسة من endpoints غير محمية على الشبكة الداخلية، أو استغلال ZAP كـ proxy هجومي.

**التوصية:**
```python
import ipaddress
from urllib.parse import urlparse
import socket

BLOCKED_HOSTS = {"localhost", "mongodb", "backend-api", "ai-analyzer", "owasp-zap"}

def _is_safe_target(url: str) -> bool:
    host = urlparse(url).hostname
    if not host or host.lower() in BLOCKED_HOSTS:
        return False
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(host))
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return False
    except (socket.gaierror, ValueError):
        return False
    return True
```
يُستدعى `_is_safe_target()` قبل `_validate_url_reachable()` مباشرة، ويُرفض الطلب بـ `400 Bad Request` عند الفشل.

---

### 2.2 🔴 قيمة افتراضية ضعيفة لـ JWT_SECRET

**الموقع:** `backend-api/app/core/config.py` (`JWT_SECRET: str = "supersecretkey"`) و `docker-compose.yml` (`JWT_SECRET=${JWT_SECRET:-supersecretkey}`)

**الوصف:** إذا نُشر المشروع دون ضبط `.env` بشكل صحيح، يبقى المفتاح ثابتًا ومعروفًا للجميع (موجود في الكود المصدري العلني على GitHub)، مما يسمح بتزوير أي JWT token والانتحال كأي مستخدم.

**التأثير:** Full authentication bypass — إمكانية تزوير token لأي `user_id` والوصول لكل تقارير أي مستخدم.

**التوصية:**
```python
import sys

class Settings(BaseSettings):
    JWT_SECRET: str = Field(..., min_length=32)  # لا قيمة افتراضية — إجباري

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.JWT_SECRET == "supersecretkey":
            print("❌ FATAL: JWT_SECRET is using the insecure default value.")
            sys.exit(1)
```
وإزالة `:-supersecretkey}` من `docker-compose.yml` ليفشل الإقلاع صراحةً بدون قيمة حقيقية.

---

### 2.3 🟠 غياب Rate Limiting على مسارات المصادقة

**الموقع:** `backend-api/app/api/auth.py` (`/login`, `/register`)

**الوصف:** لا يوجد أي حد لعدد محاولات تسجيل الدخول الفاشلة لكل IP أو لكل بريد إلكتروني، مما يسمح بهجمات Brute Force أو Credential Stuffing دون أي عائق.

**التوصية:** إضافة `slowapi` (مكتبة rate limiting متوافقة مع FastAPI):
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: UserLogin):
    ...
```

---

### 2.4 🟠 سياسة كلمة مرور ضعيفة

**الموقع:** `backend-api/app/models/user.py` — `UserCreate.password` (`min_length=6`)

**الوصف:** 6 أحرف فقط دون أي شرط تعقيد (أرقام/رموز/حروف كبيرة) يجعل الحسابات عرضة لتخمين كلمات المرور، خصوصًا مع غياب Rate Limiting (البند 2.3).

**التوصية:** رفع الحد الأدنى إلى 8 أحرف مع `field_validator` يتحقق من وجود رقم وحرف كبير على الأقل:
```python
from pydantic import field_validator

@field_validator("password")
@classmethod
def validate_password_strength(cls, v: str) -> str:
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not any(c.isdigit() for c in v):
        raise ValueError("Password must contain at least one digit")
    if not any(c.isupper() for c in v):
        raise ValueError("Password must contain at least one uppercase letter")
    return v
```

---

### 2.5 🟠 بيانات اتصال قاعدة البيانات في ملف بجذر المشروع

**الموقع:** `test_db.py` (جذر المستودع) — `mongodb://root:example@localhost:27017/`

**الوصف:** رغم أن بيانات الدخول تبدو افتراضية لبيئة تطوير محلية، وجود سكربت تصحيح (debug script) بهذا الشكل في جذر الريبو العلني يُعد ممارسة سيئة — يعطي انطباعًا خاطئًا عن نمط بيانات الاعتماد المستخدم ويشجّع على تكراره في بيئات أخرى.

**التوصية:** نقل الملف إلى `scripts/debug/` أو `.local/` وإضافته إلى `.gitignore`، أو حذفه إن لم يعد مطلوبًا.

---

### 2.6 🟡 عدم تقسيم تنبيهات ZAP الكبيرة قبل إرسالها للذكاء الاصطناعي

**الموقع:** `ai-analyzer/analyzer.py` — `_analyze_with_ai()`

**الوصف:** جميع الـ alerts (حتى لو كانت المئات، كما في `reports_output.json` حيث سُجّل فحص واحد بـ 177 ثغرة) تُرسل دفعة واحدة لـ GPT-4o بحد `max_tokens=4000` للاستجابة. هذا قد يتجاوز حدود الـ context أو ينتج استجابة JSON مقتطعة تفشل في `json.loads()`، فيسقط النظام على `_generate_fallback_analysis()` ويفقد قيمة التحليل الذكي لبقية الثغرات.

**التوصية:** تقسيم الـ alerts إلى دفعات (مثلاً 20 ثغرة لكل استدعاء) عند تجاوز عتبة معيّنة، مع تجميع النتائج قبل إعادتها للـ backend.

---

### 2.7 🟡 ملفات مخرجات فحص غير مستبعدة من المستودع

**الموقع:** جذر المشروع — `reports_output.json` (~485 KB), `scans_output.json`

**الوصف:** هذه ملفات بيانات فحص فعلية محفوظة على القرص، وغير مدرجة في `.gitignore`. لا ضرر أمني مباشر (البيانات محلية وليست أسرارًا)، لكنها تضخّم حجم المستودع دون فائدة.

**التوصية:** إضافة `*.json` استثناءً محدّدًا أو `/reports_output.json` و `/scans_output.json` صراحة إلى `.gitignore`.

---

## 3. نقاط القوة الملاحظة

- **BOLA/IDOR Protection حقيقي:** كل من `GET /api/scan/{scan_id}`، `GET /api/reports/{report_id}`، و `DELETE /api/reports/{report_id}` يتحقق فعليًا من تطابق `user_id` قبل إرجاع أو حذف أي بيانات.
- **فصل الاكتشاف عن التحليل:** الذكاء الاصطناعي (`ai-analyzer`) لا يملك صلاحية إضافة أو حذف ثغرات من نتائج ZAP الخام — فقط يُصنّف ويُفسّر ما تم اكتشافه فعليًا، ما يمنع "هلوسة" النموذج من التأثير على دقة الفحص.
- **تشفير كلمات المرور بـ bcrypt عبر `passlib`** بشكل قياسي وصحيح.
- **Fallback analysis** عند فشل تحليل استجابة الذكاء الاصطناعي — النظام لا ينهار حتى بدون AI.
- **الأسرار تُمرَّر عبر متغيرات البيئة** فقط (`JWT_SECRET`, `OPENAI_API_KEY`) — لا يوجد hardcoding فعلي داخل الكود نفسه.

---

## 4. جدول الأولويات المقترح للإصلاح

| الأولوية | البند | الجهد التقديري |
|:---:|---|:---:|
| 1 | إجبار `JWT_SECRET` (البند 2.2) | صغير — سطور قليلة |
| 2 | حظر SSRF في `security-scanner` (البند 2.1) | صغير-متوسط |
| 3 | Rate limiting على `/api/auth` (البند 2.3) | صغير |
| 4 | تعقيد كلمة المرور (البند 2.4) | صغير |
| 5 | Batching لتحليل الذكاء الاصطناعي (البند 2.6) | متوسط |
| 6 | تنظيف الملفات (البنود 2.5 و 2.7) | صغير |

---

## 5. الخاتمة

المشروع في حالة جيدة من ناحية البنية المعمارية ونمط تطبيق ضوابط الوصول. أبرز نقطتين تستحقان معالجة فورية قبل أي نشر خارج بيئة التطوير المحلية هما **SSRF** و**JWT_SECRET الافتراضي**، وكلاهما يمكن إصلاحهما بتغييرات صغيرة نسبيًا في الكود. بقية الملاحظات تحسينات جودة ودفاع متعمق (defense in depth) لا تشكل خطرًا فوريًا لكنها تستحق المعالجة قبل الاعتماد على المشروع في بيئة إنتاج حقيقية.

---

*تم إعداد هذا التقرير عبر مراجعة كود ثابتة (Static Review) دون تشغيل فعلي للنظام أو اختبار اختراق (Penetration Testing). يُنصح بإجراء اختبار ديناميكي فعلي (باستخدام WebGuard AI نفسه على نسخة staging مثلاً) للتحقق من عدم وجود ثغرات إضافية في وقت التشغيل.*