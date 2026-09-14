"""
WebGuard AI — Core Configuration
=================================
يقرأ جميع المتغيرات البيئية ويوفرها كـ Singleton لجميع أجزاء التطبيق.
يستخدم pydantic-settings للتحقق التلقائي من القيم عند بدء التشغيل.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """إعدادات النظام المركزية — تُقرأ من متغيرات البيئة أو ملف .env"""

    # ─── قاعدة البيانات ───
    MONGO_URI: str = "mongodb://mongodb:27017/webguard_db"

    # ─── عناوين الخدمات الداخلية ───
    AI_SERVICE_URL: str = "http://ai-analyzer:8011"
    SCANNER_SERVICE_URL: str = "http://security-scanner:8012"

    # ─── الأمان والمصادقة ───
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


@lru_cache()
def get_settings() -> Settings:
    """
    يُرجع نسخة واحدة (Singleton) من الإعدادات.
    يستخدم lru_cache لتجنب إعادة قراءة المتغيرات البيئية في كل طلب.
    """
    return Settings()
