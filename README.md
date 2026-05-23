# 🤖 Challenge Bot

Online challenge'ni boshqarish uchun Telegram bot.

## 📦 O'rnatish

### 1. Python o'rnatish
Python 3.10+ kerak: https://python.org

### 2. Bog'liqliklarni o'rnatish
```bash
pip install -r requirements.txt
```

### 3. .env faylini sozlash
```bash
cp .env.example .env
```
`.env` faylini oching va to'ldiring:
```
BOT_TOKEN=<BotFather dan olingan token>
ADMIN_ID=<sizning Telegram ID raqamingiz>
```

> Telegram ID ni bilish uchun @userinfobot ga yozing.

### 4. Botni ishga tushirish
```bash
python main.py
```

---

## 🗂 Bot tuzilishi

```
challenge_bot/
├── main.py              # Asosiy ishga tushirish fayli
├── database.py          # Ma'lumotlar bazasi (SQLite)
├── keyboards.py         # Tugmalar
├── states.py            # FSM holatlari
├── handlers_admin.py    # Admin panel
├── handlers_coordinator.py  # Coordinator panel
├── handlers_inspector.py    # Inspektor panel
├── handlers_user.py     # Foydalanuvchi panel
├── requirements.txt
└── .env.example
```

---

## 👥 Panellar

### 🔑 Admin Panel
`/admin` buyrug'i orqali kirish.

| Bo'lim | Imkoniyatlar |
|--------|-------------|
| Missialar | Qo'shish, tekshirish, o'chirish |
| Users | Ro'yxat (JSON), qidirish, guruhdan qidirish, ball boshqarish |
| Reyting | Top 50 |
| Inspektorlar | Tayinlash, o'chirish |
| Coordinators | Tayinlash, o'chirish |
| Guruhga tayinlash | Coordinatorni guruhga biriktirish |
| Hammaga habar | Barcha userlarga broadcast |
| Arxiv Missialar | Baholangan topshiriqlarni ko'rish |

### 🤝 Coordinator Panel
Coordinator bo'lgan telegram ID ga `/start` orqali kirish.

| Bo'lim | Imkoniyatlar |
|--------|-------------|
| Missialar | O'z guruhidagi topshiriqlarni ko'rish va baholash |
| Users | O'z guruhidagi userslar, ball boshqarish |
| Reyting | Top 50 |
| Arxiv Missialar | Baholangan topshiriqlar |

### 🔍 Inspektor Panel
Inspektor bo'lgan telegram ID ga `/start` orqali kirish.

| Bo'lim | Imkoniyatlar |
|--------|-------------|
| Missialar | Guruh + missiya raqami orqali natijalarni ko'rish |

### 👤 Foydalanuvchi Panel
`/start` bilan ro'yxatdan o'tish.

| Bo'lim | Imkoniyatlar |
|--------|-------------|
| Missialar | Ko'rish, topshirish, baho natijasini ko'rish |
| Profilim | Ma'lumotlar, tahrirlash |
| Reyting | Top 50 |
| Bot Haqida | Yordam ma'lumoti |

---

## 🏆 Ball hisoblash tizimi
Har bir missiya 2 mezon bo'yicha baholanadi:
- **Sifat**: 1-10 ball
- **Vaqt**: 1-10 ball
- **Jami**: `(Sifat + Vaqt) / 2`

---

## 📝 Eslatmalar
- Foydalanuvchilar ro'yxatdan o'tganda avtomatik 25 ta guruhga bo'linadi
- Har bir guruhga maksimal 2 ta coordinator tayinlash mumkin
- Bot ma'lumotlari `challenge_bot.db` SQLite faylida saqlanadi
