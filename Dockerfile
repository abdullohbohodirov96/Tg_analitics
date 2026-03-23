FROM python:3.11-slim

WORKDIR /app

# Dependency larni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ilova fayllarini ko'chirish
COPY app/ ./app/
COPY dashboard/ ./dashboard/

# Railway port kiritadi, lekin default qilib qo'yish zarar qilmaydi
EXPOSE 8000
ENV PORT=8000

# Start skriptini nusxalash va ishga tushirish huquqini berish
COPY start.sh .
RUN chmod +x start.sh

# Ilovani ishga tushirish
CMD ["./start.sh"]
