# استخدام نفس نسخة بايثون الخفيفة لضمان تجانس بيئة العمل
FROM python:3.10-slim

# منع بايثون من كتابة ملفات الكاش وتفعيل طباعة السجلات
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# تحديد مجلد العمل داخل الحاوية
WORKDIR /app

# استراتيجية Layer Caching: نسخ ملف المتطلبات أولاً
COPY requirements.txt .

# تحديث pip وتثبيت مكتبات الذكاء الاصطناعي الثقيلة
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع (مثل analyzer.py ومجلد prompts)
COPY . .

# فتح المنفذ المعتمد لخدمة الذكاء الاصطناعي حسب خريطة المنافذ
EXPOSE 8011

# أمر تشغيل الخدمة باستخدام Uvicorn على المنفذ 8011
# نفترض هنا أن الكود الأساسي مكتوب داخل ملف اسمه analyzer.py
CMD ["uvicorn", "analyzer:app", "--host", "0.0.0.0", "--port", "8011"]