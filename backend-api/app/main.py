"""
WebGuard AI — Main Backend Application
========================================
نقطة انطلاق الخادم المركزي (FastAPI).
يربط جميع المكونات: الـ Routers، قاعدة البيانات، الـ Middleware، و CORS.

التشغيل:
    uvicorn app.main:app --host 0.0.0.0 --port 8010
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import connect_db, close_db
from app.api import auth, scan, reports


# ═══════════════════════════════════════════
#  إدارة دورة حياة التطبيق (Startup / Shutdown)
# ═══════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    يُدير دورة حياة التطبيق:
    - عند البدء: يتصل بقاعدة البيانات
    - عند الإغلاق: يُغلق الاتصال بشكل نظيف
    """
    # ─── Startup ───
    print("🚀 جاري تشغيل WebGuard AI Backend...")
    await connect_db()
    print("✅ الخادم المركزي جاهز للعمل")
    yield
    # ─── Shutdown ───
    print("🛑 جاري إيقاف الخادم...")
    await close_db()
    print("👋 تم إيقاف الخادم بنجاح")


# ═══════════════════════════════════════════
#  إنشاء تطبيق FastAPI
# ═══════════════════════════════════════════

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "🛡️ منصة WebGuard AI — نظام ذكي لفحص الثغرات الأمنية\n\n"
        "يجمع بين قوة محرك OWASP ZAP لاكتشاف الثغرات "
        "والذكاء الاصطناعي (LangChain + OpenAI) لتحليل النتائج وتبسيطها.\n\n"
        "**مشروع تخرج — جامعة المعرفة**"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ═══════════════════════════════════════════
#  إعداد CORS — للسماح للـ Frontend بالاتصال
# ═══════════════════════════════════════════

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3030",     # Frontend (Development)
        "http://127.0.0.1:3030",
        "http://frontend:3030",      # Frontend (Docker)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════
#  تسجيل الـ Routers (المسارات)
# ═══════════════════════════════════════════

app.include_router(auth.router)
app.include_router(scan.router)
app.include_router(reports.router)


# ═══════════════════════════════════════════
#  المسارات العامة (لا تحتاج مصادقة)
# ═══════════════════════════════════════════

@app.get(
    "/",
    tags=["🏠 عام"],
    summary="الصفحة الرئيسية",
)
async def root():
    """ترحيب وتأكيد عمل الخادم."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "message": "مرحباً بك في WebGuard AI API 🛡️",
        "docs": "/docs",
    }


@app.get(
    "/health",
    tags=["🏠 عام"],
    summary="فحص صحة الخادم",
)
async def health_check():
    """نقطة فحص صحة الخادم — تُستخدم من Docker و monitoring."""
    from app.services.scanner_client import check_scanner_health
    from app.services.ai_client import check_ai_health

    scanner_ok = await check_scanner_health()
    ai_ok = await check_ai_health()

    return {
        "status": "ok",
        "services": {
            "database": "connected",
            "scanner": "available" if scanner_ok else "unavailable",
            "ai_analyzer": "available" if ai_ok else "unavailable",
        },
    }
