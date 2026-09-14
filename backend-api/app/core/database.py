"""
WebGuard AI — Database Connection (MongoDB + Motor)
=====================================================
يدير الاتصال بقاعدة بيانات MongoDB باستخدام Motor (async driver).
يوفر دوال connect/close تُستدعى عند بدء/إيقاف التطبيق.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings

# ─── المتغيرات العامة لقاعدة البيانات ───
client: AsyncIOMotorClient = None
database = None


async def connect_db():
    """
    يُنشئ اتصالاً بـ MongoDB عند بدء تشغيل التطبيق.
    يُستدعى في حدث startup الخاص بـ FastAPI.
    """
    global client, database
    settings = get_settings()
    client = AsyncIOMotorClient(settings.MONGO_URI)
    database = client.webguard_db
    # التحقق من نجاح الاتصال
    try:
        await client.admin.command("ping")
        print("✅ تم الاتصال بقاعدة البيانات MongoDB بنجاح")
    except Exception as e:
        print(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
        raise


async def close_db():
    """
    يُغلق الاتصال بـ MongoDB عند إيقاف التطبيق.
    يُستدعى في حدث shutdown الخاص بـ FastAPI.
    """
    global client
    if client:
        client.close()
        print("🔌 تم إغلاق الاتصال بقاعدة البيانات")


def get_database():
    """يُرجع مرجع قاعدة البيانات لاستخدامه في الـ Endpoints."""
    return database


def get_collection(name: str):
    """يُرجع مجموعة (Collection) محددة من قاعدة البيانات."""
    return database[name]
