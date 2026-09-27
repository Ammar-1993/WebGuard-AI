"""
WebGuard AI — Rate Limiting Configuration
============================================
يوفر Limiter مركزي (slowapi) يُستخدم لحماية نقاط المصادقة من هجمات
Brute Force / Credential Stuffing (Security Review — البند 3).

لماذا /login و /register تحديدًا:
  - /login: بدون حد، يمكن تجربة آلاف كلمات المرور على حساب واحد في وقت
    قصير جدًا (Brute Force)، خصوصًا مع سياسة كلمة المرور الحالية
    (6 أحرف فقط — انظر البند 4 من المراجعة).
  - /register: بدون حد، يمكن إنشاء آلاف الحسابات المزيفة تلقائيًا
    (Spam / Resource Exhaustion على MongoDB).

القيم قابلة للضبط عبر متغيرات بيئة دون تعديل الكود.

التخزين المشترك (Distributed Rate Limiting — Priority 4):
  يتم تخزين عدادات الـ Rate Limiting في Redis عبر storage_uri لتتبع
  محاولات تسجيل الدخول وإنشاء الحسابات بشكل موحد وتراكمي عبر جميع
  نسخ الحاوية (Container Replicas) في بيئة التوسع الأفقي (Horizontal Scaling).
"""

import logging
import os

from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger("webguard-ratelimit")

# ─── قراءة إعدادات التخزين المشترك من البيئة ───
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# ─── Limiter المركزي — التخزين الموزع عبر Redis ───
# المفتاح الأساسي هو عنوان IP الخاص بالطالب (get_remote_address)
# ويتم تخزين وتتبع العدادات في Redis لضمان عدم تجاوز الحدود عند تعدد الحاويات
if REDIS_URL:
    try:
        limiter = Limiter(
            key_func=get_remote_address,
            storage_uri=REDIS_URL,
        )
        logger.info("Initialized distributed rate limiter with Redis backend (%s)", REDIS_URL)
    except Exception as e:
        logger.warning(
            "Could not initialize Redis storage for rate limiter: %s. Falling back to in-memory storage.",
            e,
        )
        limiter = Limiter(key_func=get_remote_address)
else:
    limiter = Limiter(key_func=get_remote_address)

# ─── حدود قابلة للضبط عبر البيئة (بصيغة slowapi: "عدد/وحدة الزمن") ───
LOGIN_RATE_LIMIT = os.getenv("LOGIN_RATE_LIMIT", "5/minute")
REGISTER_RATE_LIMIT = os.getenv("REGISTER_RATE_LIMIT", "3/hour")