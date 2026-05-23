"""
🛒 Do'kon — foydalanuvchilar ballarini mahsulotlarga almashtiradi.
Admin/coordinator — xaridlar tarixini ko'radi, VIP bekor qiladi.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

import database as db
import keyboards as kb
from shop import SHOP_ITEMS, get_item

router = Router()


# ── Tugmalar ───────────────────────────────────────────────────
def shop_inline_kb():
    builder = InlineKeyboardBuilder()
    for item in SHOP_ITEMS:
        builder.button(
            text=f"{item['emoji']} {item['name']} — {item['price']} ball",
            callback_data=f"shop_buy:{item['id']}"
        )
    builder.adjust(1)
    return builder.as_markup()

def confirm_buy_kb(item_id: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, xarid qilaman", callback_data=f"shop_confirm:{item_id}")
    builder.button(text="❌ Bekor qilish", callback_data="shop_cancel")
    builder.adjust(2)
    return builder.as_markup()

def admin_shop_kb():
    kb_b = ReplyKeyboardBuilder()
    kb_b.button(text="📋 Xaridlar tarixi")
    kb_b.button(text="👑 VIP ro'yxati")
    kb_b.button(text="🔙 Orqaga")
    kb_b.adjust(2)
    return kb_b.as_markup(resize_keyboard=True)


# ── Rol aniqlash ───────────────────────────────────────────────
async def get_role(uid: int) -> str:
    from handlers_admin import is_admin
    if is_admin(uid): return "admin"
    if await db.get_coordinator(uid): return "coordinator"
    if await db.get_inspector(uid): return "inspector"
    if await db.get_user(uid): return "user"
    return "none"


# ── Do'kon (user) ──────────────────────────────────────────────
@router.message(F.text == "🛒 Do'kon")
async def shop_menu(msg: Message):
    uid = msg.from_user.id
    role = await get_role(uid)

    if role == "user":
        user = await db.get_user(uid)
        vip_badge = " 👑 VIP" if user["is_vip"] else ""
        text = (
            f"🛒 <b>Do'kon</b>{vip_badge}\n\n"
            f"💰 Sizning balingiz: <b>{user['score']}</b>\n\n"
            "Quyidagi mahsulotlardan birini tanlang:"
        )
        lines = []
        for item in SHOP_ITEMS:
            status = "✅" if user["score"] >= item["price"] else "🔒"
            lines.append(f"{status} {item['emoji']} <b>{item['name']}</b> — {item['price']} ball\n   {item['description']}")
        text += "\n\n" + "\n\n".join(lines)
        await msg.answer(text, parse_mode="HTML", reply_markup=shop_inline_kb())

    elif role in ("admin", "coordinator"):
        purchases = await db.get_all_purchases(50)
        if not purchases:
            return await msg.answer("Hali hech qanday xarid yo'q.", reply_markup=admin_shop_kb())
        await msg.answer("🛒 Do'kon boshqaruvi:", reply_markup=admin_shop_kb())


# ── Xarid bosish (user) ────────────────────────────────────────
@router.callback_query(F.data.startswith("shop_buy:"))
async def shop_buy_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    user = await db.get_user(uid)
    if not user:
        return await cb.answer("Avval ro'yxatdan o'ting!")
    item_id = cb.data.split(":")[1]
    item = get_item(item_id)
    if not item:
        return await cb.answer("Mahsulot topilmadi!")

    if user["score"] < item["price"]:
        await cb.answer(
            f"❌ Balingiz yetarli emas!\nKerak: {item['price']} | Sizda: {user['score']}",
            show_alert=True
        )
        return

    # VIP ni qayta sotib olish mumkin emas
    if item_id == "vip" and user["is_vip"]:
        await cb.answer("Sizda allaqachon VIP bor! 👑", show_alert=True)
        return

    text = (
        f"🛒 Xarid tasdiqlash\n\n"
        f"{item['emoji']} <b>{item['name']}</b>\n"
        f"💰 Narxi: <b>{item['price']} ball</b>\n"
        f"📊 Joriy balingiz: <b>{user['score']}</b>\n"
        f"📊 Xariddan keyin: <b>{user['score'] - item['price']}</b>\n\n"
        f"Xarid qilishni tasdiqlaysizmi?"
    )
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=confirm_buy_kb(item_id))
    await cb.answer()


# ── Xaridni tasdiqlash ─────────────────────────────────────────
@router.callback_query(F.data.startswith("shop_confirm:"))
async def shop_confirm_cb(cb: CallbackQuery, bot: Bot):
    uid = cb.from_user.id
    item_id = cb.data.split(":")[1]
    item = get_item(item_id)
    if not item:
        return await cb.answer("Mahsulot topilmadi!")

    old_level, result = await db.buy_item(uid, item_id, item["name"], item["price"])

    if result == "not_enough":
        await cb.message.edit_text("❌ Xarid amalga oshmadi — balingiz yetarli emas.")
        return await cb.answer()

    # Muvaffaqiyatli xarid
    user = await db.get_user(uid)
    success_text = (
        f"✅ Xarid muvaffaqiyatli!\n\n"
        f"{item['emoji']} <b>{item['name']}</b> sotib olindi!\n"
        f"💰 Sarflangan: <b>{item['price']} ball</b>\n"
        f"💳 Qolgan balingiz: <b>{user['score']}</b>"
    )
    if item_id == "vip":
        success_text += "\n\n👑 VIP belgingiz faollashdi! Profil va reytingda ko'rinadi."

    # Daraja tushib ketdimi?
    if old_level and isinstance(result, str) and result != "not_enough":
        success_text += f"\n\n📉 Daraja: {old_level} ➜ {result}"

    await cb.message.edit_text(success_text, parse_mode="HTML")
    await cb.answer("✅ Xarid amalga oshdi!")

    # Admin va coordinatorlarga xabar
    admins_coords = []
    from handlers_admin import ADMIN_IDS
    admins_coords.extend(ADMIN_IDS)
    coords = await db.get_coordinators()
    admins_coords.extend([c["telegram_id"] for c in coords])

    notif_text = (
        f"🛒 Yangi xarid!\n"
        f"👤 {user['full_name']} (Guruh #{user['group_id']})\n"
        f"🆔 {uid}\n"
        f"{item['emoji']} {item['name']} — {item['price']} ball"
    )
    for admin_id in set(admins_coords):
        try:
            await bot.send_message(admin_id, notif_text)
        except Exception:
            pass


@router.callback_query(F.data == "shop_cancel")
async def shop_cancel_cb(cb: CallbackQuery):
    user = await db.get_user(cb.from_user.id)
    vip_badge = " 👑 VIP" if user and user["is_vip"] else ""
    score = user["score"] if user else 0
    text = (
        f"🛒 <b>Do'kon</b>{vip_badge}\n\n"
        f"💰 Sizning balingiz: <b>{score}</b>\n\n"
        "Quyidagi mahsulotlardan birini tanlang:"
    )
    lines = []
    for item in SHOP_ITEMS:
        status = "✅" if score >= item["price"] else "🔒"
        lines.append(f"{status} {item['emoji']} <b>{item['name']}</b> — {item['price']} ball\n   {item['description']}")
    text += "\n\n" + "\n\n".join(lines)
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=shop_inline_kb())
    await cb.answer("Bekor qilindi")


# ── Xaridlar tarixi (admin/coordinator) ───────────────────────
@router.message(F.text == "📋 Xaridlar tarixi")
async def purchases_history(msg: Message):
    uid = msg.from_user.id
    role = await get_role(uid)
    if role not in ("admin", "coordinator"):
        return
    purchases = await db.get_all_purchases(50)
    if not purchases:
        return await msg.answer("Hali xarid yo'q.", reply_markup=admin_shop_kb())
    text = "🛒 Oxirgi 50 ta xarid:\n\n"
    for p in purchases:
        text += (
            f"👤 {p['full_name']} (Guruh #{p['group_id']})\n"
            f"🛍 {p['item_name']} — {p['price']} ball\n"
            f"📅 {p['created_at']}\n\n"
        )
    # Uzun bo'lsa bo'laklarga bo'lib yuborish
    if len(text) > 4000:
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            await msg.answer(chunk)
    else:
        await msg.answer(text)
    await msg.answer("Menyu", reply_markup=admin_shop_kb())


# ── VIP ro'yxati (admin/coordinator) ──────────────────────────
@router.message(F.text == "👑 VIP ro'yxati")
async def vip_list(msg: Message):
    uid = msg.from_user.id
    role = await get_role(uid)
    if role not in ("admin", "coordinator"):
        return
    users = await db.get_all_users()
    vip_users = [u for u in users if u["is_vip"]]
    if not vip_users:
        return await msg.answer("Hozircha VIP foydalanuvchi yo'q.", reply_markup=admin_shop_kb())
    lines = [f"👑VIP | {u['full_name']} | 🆔 {u['telegram_id']} | ⭐ {u['score']}" for u in vip_users]

    # Admin uchun VIP bekor qilish tugmasi
    from handlers_admin import is_admin
    if is_admin(uid):
        builder = InlineKeyboardBuilder()
        for u in vip_users:
            builder.button(
                text=f"❌ {u['full_name']} VIP bekor",
                callback_data=f"revoke_vip:{u['telegram_id']}"
            )
        builder.adjust(1)
        await msg.answer(
            f"👑 VIP foydalanuvchilar ({len(vip_users)} ta):\n\n" + "\n".join(lines),
            reply_markup=builder.as_markup()
        )
    else:
        await msg.answer(f"👑 VIP foydalanuvchilar ({len(vip_users)} ta):\n\n" + "\n".join(lines))
    await msg.answer("Menyu", reply_markup=admin_shop_kb())


@router.callback_query(F.data.startswith("revoke_vip:"))
async def revoke_vip_cb(cb: CallbackQuery, bot: Bot):
    from handlers_admin import is_admin
    if not is_admin(cb.from_user.id):
        return await cb.answer("Ruxsat yo'q!")
    target_id = int(cb.data.split(":")[1])
    await db.revoke_vip(target_id)
    await cb.message.edit_text(cb.message.text + f"\n\n✅ {target_id} — VIP bekor qilindi.")
    try:
        await bot.send_message(target_id, "ℹ️ Sizning VIP statusingiz admin tomonidan bekor qilindi.")
    except Exception:
        pass
    await cb.answer("VIP bekor qilindi!")


# ── Xaridlar tarixi (user — o'z xaridlari) ────────────────────
@router.message(F.text == "🧾 Xaridlarim")
async def my_purchases(msg: Message):
    uid = msg.from_user.id
    if not await db.get_user(uid):
        return
    purchases = await db.get_user_purchases(uid)
    if not purchases:
        return await msg.answer("Siz hali hech narsa sotib olmadingiz.")
    text = "🧾 Sizning xaridlaringiz:\n\n"
    for p in purchases:
        text += f"{p['item_name']} — {p['price']} ball\n📅 {p['created_at']}\n\n"
    await msg.answer(text)
