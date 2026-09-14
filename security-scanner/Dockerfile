# استخدام نسخة بايثون الخفيفة والمستقرة
FROM python:3.10-slim

# ضبط المتغيرات البيئية لتحسين الأداء ومنع الكاش
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# تحديد مجلد العمل
WORKDIR /app

# نسخ ملف المتطلبات واستغلال الكاش
COPY requirements.txt .

# تحديث pip وتثبيت مكتبات الفحص والاتصال
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# نسخ جميع السكربتات (مثل scanner_engine.py)
COPY . .

# فتح المنفذ المعتمد لخدمة الفحص 
EXPOSE 8012

# تشغيل الخدمة باستخدام Uvicorn على المنفذ 8012
# نفترض هنا أن الكود الأساسي مكتوب داخل ملف اسمه scanner_engine.py
CMD ["uvicorn", "scanner_engine:app", "--host", "0.0.0.0", "--port", "8012"]