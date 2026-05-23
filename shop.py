# Do'kon mahsulotlari

SHOP_ITEMS = [
    {
        "id": "vip",
        "name": "VIP Obuna",
        "description": "Profilingizda hamda reytingda maxsus 👑 VIP belgisi va 50% ga ko'proq ballar",
        "price": 150,
        "emoji": "👑",
    },
    {
        "id": "book",
        "name": "Kitob",
        "description": "Maxsus kitob sovg'a",
        "price": 500,
        "emoji": "📚",
    },
    {
        "id": "premium",
        "name": "Telegram Premium",
        "description": "1 oylik Telegram Premium obuna",
        "price": 800,
        "emoji": "⭐",
    },
    {
        "id": "travel",
        "name": "Bepul Sayohat",
        "description": "O'zbekiston bo'ylab maxsus sayohat sovg'asi",
        "price": 1000,
        "emoji": "✈️",
    },
]


def get_item(item_id: str):
    for item in SHOP_ITEMS:
        if item["id"] == item_id:
            return item
    return None
