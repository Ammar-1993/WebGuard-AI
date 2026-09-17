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

قيد معروف (Known Limitation — التخزين):
  التخزين الافتراضي هنا في الذاكرة (in-memory)، ويعمل بشكل صحيح فقط
  عندما تعمل نسخة واحدة من backend-api (وهو وضع docker-compose.yml
  الحالي — بدون replicas). لو تم توسيع الخدمة لعدة نسخ خلف موازن حمل،
  يجب الانتقال لتخزين مشترك (مثل Redis) عبر تمرير storage_uri عند
  إنشاء Limiter، حتى تُطبَّق الحدود على مستوى كل الحاويات معًا بدل كل
  حاوية منفردة.
"""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

# ─── Limiter المركزي — المفتاح هو عنوان IP الخاص بالطالب ───
limiter = Limiter(key_func=get_remote_address)

# ─── حدود قابلة للضبط عبر البيئة (بصيغة slowapi: "عدد/وحدة الزمن") ───
LOGIN_RATE_LIMIT = os.getenv("LOGIN_RATE_LIMIT", "5/minute")
REGISTER_RATE_LIMIT = os.getenv("REGISTER_RATE_LIMIT", "3/hour")