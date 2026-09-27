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
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import get_settings
from app.core.database import connect_db, close_db
from app.core.redis import connect_redis, close_redis
from app.core.rate_limit import limiter
from app.api import auth, scan, reports


# ═══════════════════════════════════════════
#  إدارة دورة حياة التطبيق (Startup / Shutdown)
# ═══════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    يُدير دورة حياة التطبيق:
    - عند البدء: يتصل بقاعدة البيانات وبـ Redis
    - عند الإغلاق: يُغلق الاتصالات بشكل نظيف
    """
    # ─── Startup ───
    print("🚀 Starting WebGuard AI Backend...")
    await connect_db()
    await connect_redis()

    # ─── ربط التقارير السابقة بمستخدميها إن وجدت ───
    try:
        from bson import ObjectId
        from app.core.database import get_collection
        reports_col = get_collection("reports")
        scans_col = get_collection("scans")
        async for rep in reports_col.find({"user_id": {"$exists": False}}):
            scan_id = rep.get("scan_id")
            if scan_id:
                try:
                    scan_doc = await scans_col.find_one({"_id": ObjectId(scan_id)})
                    if scan_doc and scan_doc.get("user_id"):
                        await reports_col.update_one(
                            {"_id": rep["_id"]},
                            {"$set": {"user_id": scan_doc["user_id"]}}
                        )
                except Exception:
                    pass
    except Exception as e:
        print(f"Warning: reports user_id backfill skipped: {e}")

    print("✅ Backend server is ready to work")
    yield
    # ─── Shutdown ───
    print("🛑 Stopping server...")
    await close_db()
    await close_redis()
    print("👋 Server stopped successfully")


# ═══════════════════════════════════════════
#  إنشاء تطبيق FastAPI
# ═══════════════════════════════════════════

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "🛡️ WebGuard AI Platform — Smart vulnerability scanning system\n\n"
        "Combines OWASP ZAP for discovery with AI (LangChain + OpenAI) for analysis."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ═══════════════════════════════════════════
#  إعداد Rate Limiting — حماية من Brute Force (البند 3 من المراجعة الأمنية)
# ═══════════════════════════════════════════

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


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
        "message": "Welcome to WebGuard AI API 🛡️",
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
    from app.core.redis import get_redis

    scanner_ok = await check_scanner_health()
    ai_ok = await check_ai_health()

    redis_ok = False
    try:
        r = await get_redis()
        if r and await r.ping():
            redis_ok = True
    except Exception:
        redis_ok = False

    return {
        "status": "ok",
        "services": {
            "database": "connected",
            "redis": "connected" if redis_ok else "unavailable",
            "scanner": "available" if scanner_ok else "unavailable",
            "ai_analyzer": "available" if ai_ok else "unavailable",
        },
    }