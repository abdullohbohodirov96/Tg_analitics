#!/bin/bash
# Railway uchun start skripti
# Asosiy dastur ishga tushishidan oldin jadvallarni yaratishni ta'minlaydi.

echo "🚀 Railway start skripti ishga tushdi..."

# Portni tekshirish
if [ -z "$PORT" ]; then
    PORT=8000
    echo "⚠️ PORT topilmadi, default 8000 ishlatiladi"
fi

echo "✅ Uvicorn ishga tushirilmoqda (Port: $PORT)..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
