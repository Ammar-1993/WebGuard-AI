# استخدام نسخة بايثون 3.10 خفيفة الحجم لضمان سرعة البناء وتقليل استهلاك موارد جهاز الطالب
FROM python:3.10-slim

# إعداد المتغيرات البيئية لمنع بايثون من كتابة ملفات الكاش وتفعيل طباعة السجلات (Logs) فوراً
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# تحديد مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملف المتطلبات أولاً 
# (هذه استراتيجية ذكية تسمى Layer Caching لكي لا يعيد دوكر تثبيت المكتبات من الصفر إذا غيرت كود بايثون فقط)
COPY requirements.txt .

# تحديث pip وتثبيت المكتبات المطلوبة بدون حفظ ملفات مؤقتة لتقليل حجم الحاوية النهائي
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع (مثل مجلد app) إلى الحاوية
COPY . .

# فتح المنفذ المعتمد للخادم المركزي 
EXPOSE 8010

# أمر تشغيل خادم FastAPI عبر Uvicorn وربطه بالمنفذ 8010
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]