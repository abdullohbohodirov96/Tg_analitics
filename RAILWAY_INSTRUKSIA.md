# 🚄 Railway.app orqali tekin ishga tushirish (Deploy)

Bu qadamlarni bajarib tizimni to'liq tekin, hech qanday server (VPS) sotib olmasdan ishga tushirasiz.

## 1-QADAM: GitHub ga yuklash
1. Kompyuteringizda yoki Vscode da **Terminal** oching
2. Shu (`azimuthal-shuttle`) papkada ekanligingizga ishonch hosil qiling
3. Quyidagi buyruqlarni yozing:
```bash
# Git ni boshlash
git init
git add .
git commit -m "First commit: Telegram Analytics System"

# GitHub.com ga kiring, yangi repository yarating (masalan "tg-analytics")
# Repository manzilini olib, quydagini yozing:
git remote add origin https://github.com/SIZNING_USERNAME/tg-analytics.git
git branch -M main
git push -u origin main
```

*(Agar GitHub tushunarsiz bo'lsa, fayllarni oddiygina GitHub saytidan yuklab qo'ysangiz ham bo'ladi)*

---

## 2-QADAM: Railway.app ga kirish
1. **[railway.app](https://railway.app/)** saytiga kiring
2. **Login** tugmasini bosib, GitHub orqali ro'yxatdan o'ting
3. **New Project** tugmasini bosing
4. **Deploy from GitHub repo** ni tanlang
5. Boya yaratgan `tg-analytics` repository ni tanlang
6. **Deploy Now** ni bosing

---

## 3-QADAM: Database (Ma'lumotlar bazasi) qo'shish
1. Railway proyekt oynangizda **+ New** tugmasini bosing
2. **Database** → **Add PostgreSQL** ni tanlang
3. Bazani yaralishini 10-15 soniya kuting

---

## 4-QADAM: Sozlamalarni ulash (Variables)
1. Endi o'zingizning Dasturingiz (App) blokiga bosing (PostgreSQL ga emas)
2. **Variables** bo'limiga o'ting
3. Quyidagi ma'lumotlarni bitta-bitta qo'shing (New Variable):

| Variable nomi | Qiymati |
|---|---|
| `BOT_TOKEN` | `8329214616:AAFvZIEuCK9RFDHpUEP77A7Mx6Wc4KKOifo` |
| `WEBHOOK_SECRET` | `tg_analytics_webhook_secret_2024` |
| `JWT_SECRET` | `jwt_super_secret_key_analytics_2024` |
| `ADMIN_USERNAME` | `admin` |
| `ADMIN_PASSWORD` | `admin123` |

*(DATABASE_URL qo'shish shart emas, Railway o'zi avtomatik ulaydi!)*

---

## 5-QADAM: Domen olish
1. App sozlamalaridan **Settings** bo'limiga o'ting
2. Pastroqqa tushsangiz **Domains** qismi bor
3. **Generate Domain** tugmasini bosing
4. U sizga tekin URL beradi (masalan: `tg-analytics-production.up.railway.app`)

---

## 6-QADAM: Telegram Botga Webhook ulash
Loyiha ishlab bo'lgach (yashil qizil emas, yashil yonishi kerak), botga shu ulanishni bildirishimiz kerak.

Brauzeringizda quyidagi manzilni oching (manzilni o'zingiznikiga almashtiring):
```
https://api.telegram.org/bot8329214616:AAFvZIEuCK9RFDHpUEP77A7Mx6Wc4KKOifo/setWebhook?url=https://SIZNING_RAILWAY_DOMENINGIZ/webhook/telegram&secret_token=tg_analytics_webhook_secret_2024
```

Masalan agar domen `tg-analytics-production.up.railway.app` bo'lsa:
```
https://api.telegram.org/bot8329214616:AAFvZIEuCK9RFDHpUEP77A7Mx6Wc4KKOifo/setWebhook?url=https://tg-analytics-production.up.railway.app/webhook/telegram&secret_token=tg_analytics_webhook_secret_2024
```

Agar ekranda `{"ok":true,"result":true,"description":"Webhook was set"}` yozuvi chiqsa — **TABRIKLAYMIZ! BARCHASI TAYYOR! 🎉**

---

### Endi qanday ishlatasiz?
1. Dashboard ga kirish uchun: `https://SIZNING_RAILWAY_DOMENINGIZ`
2. Parol: `admin` / `admin123`
3. Guruhga botni qo'shib, xabar yozsangiz hammasi ishlashni boshlaydi!
