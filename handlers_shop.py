"""
Do'kon — admin boshqaruvida mahsulotlar
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
import aiosqlite

import database as db
from database import DB_PATH
from states import AddProductStates
import keyboards as kb
from shop import SHOP_ITEMS, get_item

router = Router()





async def get_role(uid: int) -> str:
    from handlers_admin import is_admin
    if is_admin(uid): return "admin"
    if await db.get_coordinator(uid): return "coordinator"
    if await db.get_inspector(uid): return "inspector"
    if await db.get_user(uid): return "user"
    return "none"


def admin_shop_kb():
    kb_b = ReplyKeyboardBuilder()
    kb_b.button(text="➕ Mahsulot qo'shish")
    kb_b.button(text="📋 Mahsulotlar ro'yxati")
    kb_b.button(text="🧾 Xaridlar tarixi")
    kb_b.button(text="👑 VIP ro'yxati")
    kb_b.button(text="🔙 Orqaga")
    kb_b.adjust(2)
    return kb_b.as_markup(resize_keyboard=True)


def coordinator_shop_kb():
    kb_b = ReplyKeyboardBuilder()
    kb_b.button(text="🧾 Xaridlar tarixi")
    kb_b.button(text="👑 VIP ro'yxati")
    kb_b.button(text="🔙 Orqaga")
    kb_b.adjust(2)
    return kb_b.as_markup(resize_keyboard=True)


def products_inline_kb(products, shop_items, eco: float = 0):
    builder = InlineKeyboardBuilder()
    # Database mahsulotlar
    for p in products:
        status = "✅" if eco >= p["price"] else "🔒"
        builder.button(
            text=f"{status} {p['emoji']} {p['name']} — {p['price']} 🌿",
            callback_data=f"buy_product:{p['id']}"
        )
    # SHOP_ITEMS
    for item in shop_items:
        status = "✅" if eco >= item["price"] else "🔒"
        builder.button(
            text=f"{status} {item['emoji']} {item['name']} — {item['price']} 🌿",
            callback_data=f"buy_shop_item:{item['id']}"
        )
    builder.adjust(1)
    return builder.as_markup()


def confirm_buy_kb(product_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Xarid qilish", callback_data=f"confirm_product:{product_id}")
    builder.button(text="❌ Bekor", callback_data="cancel_product")
    builder.adjust(2)
    return builder.as_markup()


def confirm_buy_shop_item_kb(item_id: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Xarid qilish", callback_data=f"confirm_shop_item:{item_id}")
    builder.button(text="❌ Bekor", callback_data="cancel_product")
    builder.adjust(2)
    return builder.as_markup()


# ── 🛒 Do'kon ──────────────────────────────────────────────────
@router.message(F.text == "🛒 Do'kon")
async def shop_menu(msg: Message):
    uid = msg.from_user.id
    role = await get_role(uid)
    if role == "user":
        user = await db.get_user(uid)
        vip = " 👑 VIP" if user and user["is_vip"] else ""
        eco = user["ecopoints"] if user else 0
        await msg.answer(
            f"🛒 <b>Do'kon</b>{vip}\n🌿 EcoPoint: <b>{eco}</b>",
            parse_mode="HTML",
            reply_markup=kb.shop_menu_user()
        )
    elif role == "admin":
        await msg.answer("🛒 Do'kon boshqaruvi:", reply_markup=admin_shop_kb())
    elif role == "coordinator":
        await msg.answer("🛒 Do'kon boshqaruvi:", reply_markup=coordinator_shop_kb())


@router.message(F.text == "🛍 Mahsulotlar")
async def shop_products(msg: Message):
    uid = msg.from_user.id
    if await get_role(uid) != "user":
        return
    user = await db.get_user(uid)
    eco = user["ecopoints"] if user else 0
    products = await db.get_shop_products()
    
    lines = []
    
    # Database mahsulotlar
    if products:
        for p in products:
            status = "✅" if eco >= p["price"] else "🔒"
            lines.append(f"{status} {p['emoji']} <b>{p['name']}</b> — {p['price']} 🌿\n   {p['description']}")
    
    # SHOP_ITEMS
    for item in SHOP_ITEMS:
        status = "✅" if eco >= item["price"] else "🔒"
        lines.append(f"{status} {item['emoji']} <b>{item['name']}</b> — {item['price']} 🌿\n   {item['description']}")
    
    if not lines:
        return await msg.answer("Hozircha do'konda mahsulot yo'q.")
    
    text = (
        f"🛒 <b>Mahsulotlar</b>\n🌿 Balansingiz: <b>{eco}</b>\n\n"
        + "\n\n".join(lines)
    )
    await msg.answer(text, parse_mode="HTML", reply_markup=products_inline_kb(products or [], SHOP_ITEMS, eco))


# ── Xarid qilish ──────────────────────────────────────────────
@router.callback_query(F.data.startswith("buy_product:"))
async def buy_product_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    product_id = int(cb.data.split(":")[1])
    product = await db.get_shop_product(product_id)
    if not product:
        return await cb.answer("Mahsulot topilmadi!", show_alert=True)
    user = await db.get_user(uid)
    eco = user["ecopoints"] if user else 0
    if eco < product["price"]:
        return await cb.answer(
            f"❌ EcoPoint yetarli emas!\n🌿 Kerak: {product['price']} | Sizda: {eco}",
            show_alert=True
        )
    await cb.message.answer(
        f"🛒 <b>Xarid tasdiqlash</b>\n\n"
        f"{product['emoji']} <b>{product['name']}</b>\n"
        f"📝 {product['description']}\n"
        f"🌿 Narxi: <b>{product['price']} EcoPoint</b>\n"
        f"💰 Balansingiz: <b>{eco}</b> → <b>{eco - product['price']}</b>\n\n"
        f"Tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=confirm_buy_kb(product_id)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("buy_shop_item:"))
async def buy_shop_item_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    item_id = cb.data.split(":")[1]
    item = get_item(item_id)
    if not item:
        return await cb.answer("Mahsulot topilmadi!", show_alert=True)
    user = await db.get_user(uid)
    eco = user["ecopoints"] if user else 0
    if eco < item["price"]:
        return await cb.answer(
            f"❌ EcoPoint yetarli emas!\n🌿 Kerak: {item['price']} | Sizda: {eco}",
            show_alert=True
        )
    await cb.message.answer(
        f"🛒 <b>Xarid tasdiqlash</b>\n\n"
        f"{item['emoji']} <b>{item['name']}</b>\n"
        f"📝 {item['description']}\n"
        f"🌿 Narxi: <b>{item['price']} EcoPoint</b>\n"
        f"💰 Balansingiz: <b>{eco}</b> → <b>{eco - item['price']}</b>\n\n"
        f"Tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=confirm_buy_shop_item_kb(item_id)
    )
    await cb.answer()



@router.callback_query(F.data.startswith("confirm_product:"))
async def confirm_product_cb(cb: CallbackQuery, bot: Bot):
    uid = cb.from_user.id
    product_id = int(cb.data.split(":")[1])
    result = await db.buy_shop_product(uid, product_id)
    product = await db.get_shop_product(product_id)
    if result == "ok":
        user = await db.get_user(uid)
        await cb.message.edit_text(
            f"✅ Xarid muvaffaqiyatli!\n"
            f"{product['emoji']} <b>{product['name']}</b> sotib olindi!\n"
            f"🌿 Qolgan EcoPoint: <b>{user['ecopoints']}</b>",
            parse_mode="HTML"
        )
        await cb.answer("✅ Xarid amalga oshdi!")
        # Admin va coordinatorlarga xabar
        from handlers_admin import ADMIN_IDS
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    f"🛒 Yangi xarid!\n👤 {user['full_name']} (#{user['group_id']})\n"
                    f"{product['emoji']} {product['name']} — {product['price']} 🌿"
                )
            except Exception:
                pass
    elif result == "not_enough":
        await cb.answer("❌ EcoPoint yetarli emas!", show_alert=True)
    else:
        await cb.answer("❌ Mahsulot topilmadi!", show_alert=True)


@router.callback_query(F.data.startswith("confirm_shop_item:"))
async def confirm_shop_item_cb(cb: CallbackQuery, bot: Bot):
    uid = cb.from_user.id
    item_id = cb.data.split(":")[1]
    item = get_item(item_id)
    if not item:
        return await cb.answer("Mahsulot topilmadi!", show_alert=True)
    
    # Spend ecopoints
    result = await db.spend_ecopoints(uid, item["price"], f"Do'kondan xarid: {item['name']}")
    
    if not result:
        user = await db.get_user(uid)
        eco = user["ecopoints"] if user else 0
        return await cb.answer(
            f"❌ EcoPoint yetarli emas!\n🌿 Kerak: {item['price']} | Sizda: {eco}",
            show_alert=True
        )
    
    # VIP mahsulot sotib olinganda is_vip = 1 qo'yish
    if item_id == "vip":
        async with aiosqlite.connect(DB_PATH) as database:
            await database.execute("UPDATE users SET is_vip=1 WHERE telegram_id=?", (uid,))
            await database.commit()
    
    # Purchase historiysini saqlash
    async with aiosqlite.connect(DB_PATH) as database:
        await database.execute(
            "INSERT INTO purchases (user_telegram_id, item_id, item_name, price, status) VALUES (?,?,?,?,'completed')",
            (uid, f"shop_item_{item_id}", item['name'], item["price"])
        )
        await database.commit()
    
    user = await db.get_user(uid)
    await cb.message.edit_text(
        f"✅ Xarid muvaffaqiyatli!\n"
        f"{item['emoji']} <b>{item['name']}</b> sotib olindi!\n"
        f"🌿 Qolgan EcoPoint: <b>{user['ecopoints']}</b>",
        parse_mode="HTML"
    )
    await cb.answer("✅ Xarid amalga oshdi!")
    
    # Admin va coordinatorlarga xabar
    from handlers_admin import ADMIN_IDS
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🛒 Yangi xarid!\n👤 {user['full_name']} (#{user['group_id']})\n"
                f"{item['emoji']} {item['name']} — {item['price']} 🌿"
            )
        except Exception:
            pass


@router.callback_query(F.data == "cancel_product")
async def cancel_product_cb(cb: CallbackQuery):
    await cb.message.delete()
    await cb.answer("Bekor qilindi.")


# ── Admin: Mahsulot qo'shish ──────────────────────────────────
@router.message(F.text == "➕ Mahsulot qo'shish")
async def add_product_start(msg: Message, state: FSMContext):
    from handlers_admin import is_admin
    if not is_admin(msg.from_user.id):
        return
    await msg.answer("Mahsulot nomini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(AddProductStates.name)


@router.message(AddProductStates.name)
async def add_product_name(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=admin_shop_kb())
    await state.update_data(name=msg.text)
    await msg.answer("Tavsifini kiriting:")
    await state.set_state(AddProductStates.description)


@router.message(AddProductStates.description)
async def add_product_desc(msg: Message, state: FSMContext):
    await state.update_data(description=msg.text)
    await msg.answer("Narxini kiriting (EcoPoint):")
    await state.set_state(AddProductStates.price)


@router.message(AddProductStates.price)
async def add_product_price(msg: Message, state: FSMContext):
    try:
        price = float(msg.text)
        await state.update_data(price=price)
        await msg.answer("Emoji kiriting (masalan: 🎁 📚 👑) yoki /skip:")
        await state.set_state(AddProductStates.emoji)
    except ValueError:
        await msg.answer("Son kiriting!")


@router.message(AddProductStates.emoji)
async def add_product_emoji(msg: Message, state: FSMContext):
    emoji = "🎁"
    if msg.text and msg.text != "/skip":
        emoji = msg.text.strip()
    data = await state.get_data()
    await db.add_shop_product(data["name"], data["description"], data["price"], emoji)
    await state.clear()
    await msg.answer(
        f"✅ Mahsulot qo'shildi!\n{emoji} {data['name']} — {data['price']} 🌿",
        reply_markup=admin_shop_kb()
    )


# ── Admin: Mahsulotlar ro'yxati ───────────────────────────────
@router.message(F.text == "📋 Mahsulotlar ro'yxati")
async def products_list(msg: Message):
    from handlers_admin import is_admin
    uid = msg.from_user.id
    if not is_admin(uid) and not await db.get_coordinator(uid):
        return
    products = await db.get_shop_products()
    if not products:
        return await msg.answer("Hozircha mahsulot yo'q.", reply_markup=admin_shop_kb())
    for p in products:
        builder = InlineKeyboardBuilder()
        builder.button(text="🗑 O'chirish", callback_data=f"del_product:{p['id']}")
        await msg.answer(
            f"{p['emoji']} <b>{p['name']}</b>\n{p['description']}\n🌿 {p['price']} EcoPoint",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )


@router.callback_query(F.data.startswith("del_product:"))
async def delete_product_cb(cb: CallbackQuery):
    from handlers_admin import is_admin
    if not is_admin(cb.from_user.id):
        return await cb.answer("Ruxsat yo'q!")
    product_id = int(cb.data.split(":")[1])
    await db.delete_shop_product(product_id)
    await cb.message.edit_text("🗑 Mahsulot o'chirildi.")
    await cb.answer()


# ── Xaridlar tarixi (admin) ───────────────────────────────────
@router.message(F.text == "🧾 Xaridlar tarixi")
async def purchases_history(msg: Message):
    from handlers_admin import is_admin
    uid = msg.from_user.id
    if is_admin(uid):
        purchases = await db.get_all_purchases(50)
        rm = admin_shop_kb()
    elif await db.get_coordinator(uid):
        purchases = await db.get_purchases_for_coordinator(uid, 50)
        rm = coordinator_shop_kb()
    else:
        return
    if not purchases:
        return await msg.answer("Hali xarid yo'q.", reply_markup=rm)
    text = "🛒 <b>Oxirgi 50 ta xarid:</b>\n\n"
    for p in purchases:
        text += f"👤 {p['full_name']} | {p['item_name']} — {p['price']} 🌿 | {str(p['created_at'])[:10]}\n"
    await msg.answer(text, parse_mode="HTML")


# ── VIP ro'yxati ───────────────────────────────────────────────
@router.message(F.text == "👑 VIP ro'yxati")
async def vip_list(msg: Message):
    from handlers_admin import is_admin
    uid = msg.from_user.id
    if is_admin(uid):
        users = await db.get_all_users()
        vip_users = [u for u in users if u["is_vip"]]
        rm = admin_shop_kb()
        show_revoke = True
    elif await db.get_coordinator(uid):
        groups = await db.get_coordinator_groups(uid)
        if not groups:
            return await msg.answer("Sizga guruh tayinlanmagan.")
        all_users = await db.get_all_users()
        vip_users = [u for u in all_users if u["is_vip"] and u["group_id"] in groups]
        rm = coordinator_shop_kb()
        show_revoke = False
    else:
        return
    if not vip_users:
        return await msg.answer("Hozircha VIP foydalanuvchi yo'q.")
    lines = [f"👑 {u['full_name']} | 🆔 {u['telegram_id']} | ⭐ {u['score']}" for u in vip_users]
    if show_revoke:
        builder = InlineKeyboardBuilder()
        for u in vip_users:
            builder.button(text=f"❌ {u['full_name']} VIP bekor", callback_data=f"revoke_vip:{u['telegram_id']}")
        builder.adjust(1)
        await msg.answer(f"👑 VIP ({len(vip_users)} ta):\n\n" + "\n".join(lines), reply_markup=builder.as_markup())
    else:
        await msg.answer(f"👑 VIP ({len(vip_users)} ta):\n\n" + "\n".join(lines))


@router.callback_query(F.data.startswith("revoke_vip:"))
async def revoke_vip_cb(cb: CallbackQuery, bot: Bot):
    from handlers_admin import is_admin
    if not is_admin(cb.from_user.id):
        return await cb.answer("Ruxsat yo'q!")
    tid = int(cb.data.split(":")[1])
    await db.revoke_vip(tid)
    await cb.message.edit_text(cb.message.text + f"\n✅ {tid} VIP bekor qilindi.")
    try:
        await bot.send_message(tid, "ℹ️ VIP statusingiz bekor qilindi.")
    except Exception:
        pass
    await cb.answer()


# ── User: Xaridlarim ──────────────────────────────────────────
@router.message(F.text == "🧾 Xaridlarim")
async def my_purchases(msg: Message):
    uid = msg.from_user.id
    if not await db.get_user(uid):
        return
    purchases = await db.get_user_purchases(uid)
    if not purchases:
        return await msg.answer("Siz hali hech narsa sotib olmadingiz.")
    text = "🧾 <b>Sizning xaridlaringiz:</b>\n\n"
    for p in purchases:
        text += f"🎁 {p['item_name']} — {p['price']} 🌿\n📅 {str(p['created_at'])[:10]}\n\n"
    await msg.answer(text, parse_mode="HTML")