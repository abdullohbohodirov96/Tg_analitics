# 📊 Telegram Group Analytics System

Telegram guruhlar uchun to'liq analytics tizimi: xabarlar tahlili, operator samaradorligi, javob vaqtlari, va professional web dashboard.

## 🚀 Tez Boshlash (Quick Start)

### 1. Docker bilan ishga tushirish

```bash
# Loyihani ko'chirish
cd azimuthal-shuttle

# Docker containerlarni build qilish va ishga tushirish
docker-compose up --build -d

# Loglarni ko'rish
docker-compose logs -f app
```

### 2. Webhook o'rnatish

Server ishga tushgandan keyin, Telegram botga webhook o'rnating:

```bash
# YOUR_DOMAIN ni o'z domen yoki IP manzilingiz bilan almashtiring
python3 scripts/setup_webhook.py https://YOUR_DOMAIN
```

Yoki qo'lda:
```bash
curl -X POST "https://api.telegram.org/bot8329214616:AAFvZIEuCK9RFDHpUEP77A7Mx6Wc4KKOifo/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://YOUR_DOMAIN/webhook/telegram",
    "secret_token": "tg_analytics_webhook_secret_2024"
  }'
```

### 3. Dashboard ochish

- **Dashboard**: http://YOUR_DOMAIN (yoki http://localhost)
- **API Docs**: http://YOUR_DOMAIN/docs
- **Login**: admin / admin123

---

## 📁 Loyiha Strukturasi

```
├── app/                    # Backend (FastAPI)
│   ├── main.py            # Asosiy ilova
│   ├── config.py          # Sozlamalar
│   ├── database.py        # DB ulanish
│   ├── models/            # ORM modellari
│   ├── repositories/      # DB query lari
│   ├── services/          # Biznes logika
│   ├── routers/           # API endpointlar
│   └── utils/             # Yordamchi funksiyalar
├── dashboard/             # Frontend (HTML/CSS/JS)
│   ├── index.html         # Dashboard SPA
│   ├── login.html         # Login sahifa
│   ├── css/style.css      # Stillar
│   └── js/                # JavaScript
├── nginx/                 # Nginx konfiguratsiya
├── scripts/               # Yordamchi skriptlar
├── docker-compose.yml     # Docker compose
├── Dockerfile             # Docker image
├── .env                   # Environment variables
└── requirements.txt       # Python dependencies
```

---

## 🔧 API Endpointlar

| Endpoint | Tavsif |
|---|---|
| `POST /webhook/telegram` | Telegram webhook |
| `POST /api/auth/login` | Admin login |
| `GET /api/stats/overview` | Umumiy statistika |
| `GET /api/stats/today` | Bugungi statistika |
| `GET /api/stats/week` | Haftalik |
| `GET /api/stats/month` | Oylik |
| `GET /api/stats/operators` | Operatorlar |
| `GET /api/stats/users` | Foydalanuvchilar |
| `GET /api/stats/unanswered` | Javobsiz suhbatlar |
| `GET /api/stats/messages` | Kunlik xabarlar |
| `GET /api/stats/response-time` | Javob vaqti |
| `GET /api/stats/conversations` | Suhbatlar |
| `GET /api/stats/heatmap` | Soatlik heatmap |

Barcha `/api/stats/*` endpointlar `?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD` filterlarni qo'llab-quvvatlaydi.

---

## 🤖 Bot Buyruqlari

| Buyruq | Tavsif |
|---|---|
| `/stats` | Umumiy statistika |
| `/today` | Bugungi statistika |
| `/week` | Haftalik statistika |
| `/month` | Oylik statistika |
| `/operators` | Operatorlar natijasi |
| `/unanswered` | Javobsiz foydalanuvchilar |
| `/help` | Yordam |

---

## 🔐 Xavfsizlik

- Barcha maxfiy ma'lumotlar `.env` faylida
- Webhook `secret_token` bilan himoyalangan
- Admin panel JWT token bilan himoyalangan
- Parollar bcrypt bilan hash qilingan

---

## 🖥 VPS ga Deploy Qilish

### Talab qilinadigan narsalar:
- VPS (Ubuntu 20.04+)
- Docker va Docker Compose o'rnatilgan
- Domen nomi (ixtiyoriy, IP bilan ham ishlaydi)

### Qadamlar:

```bash
# 1. VPS ga kirish
ssh root@YOUR_SERVER_IP

# 2. Docker o'rnatish (agar o'rnatilmagan bo'lsa)
curl -fsSL https://get.docker.com | sh

# 3. Loyihani ko'chirish
git clone YOUR_REPO_URL
cd azimuthal-shuttle

# 4. .env faylni sozlash
cp .env.example .env
nano .env  # Tokenlarni kiriting

# 5. Ishga tushirish
docker-compose up --build -d

# 6. Webhook o'rnatish
python3 scripts/setup_webhook.py https://YOUR_DOMAIN
```

---

## 📊 Ishlash Logikasi

1. **Xabar keldi** → Webhook orqali qabul qilinadi → DB ga saqlanadi
2. **User yozdi** → Yangi conversation ochiladi (javobsiz holat)
3. **Operator reply qildi** → Conversation answered bo'ladi, response_time hisoblanadi
4. **Dashboard** → Barcha ma'lumotlar real-time ko'rinadi
