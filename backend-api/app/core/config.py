"""
WebGuard AI — Core Configuration
=================================
يقرأ جميع المتغيرات البيئية ويوفرها كـ Singleton لجميع أجزاء التطبيق.
يستخدم pydantic-settings للتحقق التلقائي من القيم عند بدء التشغيل.

ملاحظة أمنية (Security Review):
  JWT_SECRET كان له قيمة افتراضية ضعيفة ومعروفة ("supersecretkey") سواء هنا
  أو في docker-compose.yml. أي نشر ينسى تعيين .env بشكل صحيح كان سيصبح
  فورًا قابلاً لتزوير أي JWT token والانتحال كأي مستخدم.

  الحل هنا مبني على طبقتين:
  1. رفض أي قيمة معروفة/ضعيفة أو قصيرة لـ JWT_SECRET خارج بيئة التطوير —
     التطبيق يفشل عند الإقلاع (fail-fast) بدل أن يعمل بشكل غير آمن بصمت.
  2. حتى في بيئة التطوير، يُطبع تحذير واضح إن كانت القيمة الافتراضية
     مستخدمة، حتى لا يُنسى تغييرها لاحقًا.
"""

import secrets
import sys

from pydantic_settings import BaseSettings
from functools import lru_cache


# ─── قيم معروفة يجب رفضها دائمًا كـ JWT_SECRET حقيقي ───
INSECURE_JWT_SECRETS = {
    "supersecretkey",
    "your-super-secret-jwt-key-change-me",
    "your-secure-random-jwt-secret-key",
    "changeme",
    "secret",
}

MIN_JWT_SECRET_LENGTH = 32


class Settings(BaseSettings):
    """إعدادات النظام المركزية — تُقرأ من متغيرات البيئة أو ملف .env"""

    # ─── بيئة التشغيل ───
    # "development" هي القيمة الوحيدة التي تسمح بتشغيل مؤقت بقيمة JWT_SECRET
    # افتراضية مع تحذير. أي قيمة أخرى (production, staging, ...) تفشل فورًا
    # إن كانت القيمة غير آمنة.
    ENVIRONMENT: str = "development"

    # ─── قاعدة البيانات ───
    MONGO_URI: str = "mongodb://mongodb:27017/webguard_db"

    # ─── عناوين الخدمات الداخلية ───
    AI_SERVICE_URL: str = "http://ai-analyzer:8011"
    SCANNER_SERVICE_URL: str = "http://security-scanner:8012"

    # ─── الأمان والمصادقة ───
    # لا توجد قيمة افتراضية آمنة ممكنة لسر توقيع JWT — يجب أن تُقرأ من البيئة.
    # القيمة الافتراضية هنا موجودة فقط لتفادي انهيار pydantic قبل أن نصل
    # لفحصنا الخاص أدناه، الذي سيرفضها فورًا إن لم تُستبدل في بيئة غير تطويرية.
    JWT_SECRET: str = "supersecretkey"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60  # مدة صلاحية الـ Token (ساعة واحدة)

    # ─── إعدادات التطبيق ───
    APP_NAME: str = "WebGuard AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

    # ═══════════════════════════════════════════
    #  فحص أمني عند الإقلاع — Fail-Fast على JWT_SECRET
    # ═══════════════════════════════════════════
    #
    #  القرار موحّد في مكان واحد (model_post_init) بدل تفريقه بين عدة
    #  validators، لأن "هل هذه القيمة مقبولة؟" يعتمد على شرطين معًا:
    #  قوة القيمة نفسها (الطول/كونها معروفة) + بيئة التشغيل (ENVIRONMENT).
    #
    #  السلوك المطلوب تحديدًا (متطلب المراجعة الأمنية):
    #    - development  → قيمة ضعيفة/افتراضية؟ تحذير فقط، يستمر التشغيل
    #                      (لتسهيل التجربة السريعة محليًا).
    #    - أي بيئة أخرى → قيمة ضعيفة/افتراضية؟ رفض فوري للإقلاع (fail-fast).

    def model_post_init(self, __context) -> None:
        is_known_insecure = self.JWT_SECRET.lower() in INSECURE_JWT_SECRETS
        is_too_short = len(self.JWT_SECRET) < MIN_JWT_SECRET_LENGTH
        is_weak = is_known_insecure or is_too_short

        if not is_weak:
            return

        reason = (
            "a known insecure default value"
            if is_known_insecure
            else f"too short ({len(self.JWT_SECRET)} chars, minimum {MIN_JWT_SECRET_LENGTH})"
        )

        if self.ENVIRONMENT.lower() != "development":
            _fail_startup(
                f"JWT_SECRET is {reason} while ENVIRONMENT='{self.ENVIRONMENT}'. "
                f"Refusing to start.\n{_generation_hint()}"
            )
        else:
            print(
                f"⚠️  WARNING: JWT_SECRET is {reason}. "
                "This is only tolerated because ENVIRONMENT=development.\n"
                "   Set a real JWT_SECRET before deploying anywhere else "
                f"(ENVIRONMENT != 'development').\n   {_generation_hint()}",
                file=sys.stderr,
            )


def _generation_hint() -> str:
    """رسالة توليد قيمة آمنة — نستخدمها في رسائل الخطأ والتحذير."""
    return (
        "Generate a strong secret with:\n"
        "   python -c \"import secrets; print(secrets.token_urlsafe(48))\"\n"
        "   then set it as JWT_SECRET in your .env file."
    )


def _fail_startup(message: str) -> None:
    """يطبع خطأ واضح ويوقف إقلاع التطبيق فورًا (fail-fast)."""
    print(f"❌ FATAL CONFIG ERROR: {message}", file=sys.stderr)
    sys.exit(1)


@lru_cache()
def get_settings() -> Settings:
    """
    يُرجع نسخة واحدة (Singleton) من الإعدادات.
    يستخدم lru_cache لتجنب إعادة قراءة المتغيرات البيئية في كل طلب.
    """
    return Settings()