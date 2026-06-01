"""
🌿 EcoPoint tizimi handlerlari
  - Kundalik kirish (checkin)
  - Referral havola
  - EcoPoint tarixi va balansi
  - Admin: EcoPoint berish, missiyaga EcoPoint belgilash
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
import keyboards as kb
from ecopoint import ECOPOINT_REWARDS
from handlers_admin import is_admin

router = Router()


class AdminEcoStates(StatesGroup):
    user_id = State()
    amount = State()
    reason = State()

class MissionEcoStates(StatesGroup):
    mission_number = State()
    eco_amount = State()


async def get_role(uid: int) -> str:
    from handlers_admin import is_admin
    if is_admin(uid): return "admin"
    if await db.get_coordinator(uid): return "coordinator"
    if await db.get_inspector(uid): return "inspector"
    if await db.get_user(uid): return "user"
    return "none"


# ── /start?start=REF_ID — referral ────────────────────────────
@router.message(CommandStart(deep_link=True))
async def start_referral(msg: Message, command: CommandObject, bot: Bot, state: FSMContext):
    """Referral havola orqali kelgan user."""
    from subscription import subscription_guard
    if not await subscription_guard(msg, bot):
        return

    uid = msg.from_user.id
    args = command.args
    try:
        referrer_id = int(args.replace("ref_", ""))
    except Exception:
        return

    user = await db.get_user(uid)
    if user:
        return  # Allaqachon ro'yxatdan o'tgan

    # Referrer ni saqla, ro'yxatdan o'tish jarayoni boshlanganda qo'llanadi
    await state.update_data(referrer_id=referrer_id)
    await msg.answer(
        f"👋 Siz do'stingiz taklifi orqali keldingiz!\n"
        f"Ro'yxatdan o'tganingizdan so'ng siz va do'stingiz "
        f"<b>{ECOPOINT_REWARDS['referral']} 🌿 EcoPoint</b> olasiz!",
        parse_mode="HTML"
    )
    await msg.answer("Ro'yxatdan o'tish uchun ism-familiyangizni kiriting:", reply_markup=kb.cancel_kb())
    from states import RegisterStates
    await state.set_state(RegisterStates.full_name)


# ── 🌿 EcoPoint menyusi ────────────────────────────────────────
@router.message(F.text == "🌿 EcoPoint")
async def ecopoint_menu(msg: Message, bot: Bot):
    uid = msg.from_user.id
    role = await get_role(uid)
    if role == "none":
        return

    user = await db.get_user(uid)

    if role == "user":
        eco = user["ecopoints"] if user else 0
        bot_info = await bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref_{uid}"

        # Kundalik kirish
        checkin_done = await db.daily_checkin(uid)
        checkin_msg = ""
        if checkin_done:
            await db.add_ecopoints(uid, ECOPOINT_REWARDS["daily_checkin"], "Kundalik kirish")
            eco += ECOPOINT_REWARDS["daily_checkin"]
            checkin_msg = f"\n✅ Kundalik kirish: +{ECOPOINT_REWARDS['daily_checkin']} 🌿"

        text = (
            f"🌿 <b>EcoPoint hisobingiz</b>\n\n"
            f"💰 Balans: <b>{eco} 🌿 EcoPoint</b>{checkin_msg}\n\n"
            f"📋 <b>Qanday yig'iladi:</b>\n"
            f"  ✅ Missiya bajarish — Admin belgilagan miqdor\n"
            f"  👥 Do'st taklif qilish — {ECOPOINT_REWARDS['referral']} 🌿\n"
            f"  📅 Kundalik kirish — {ECOPOINT_REWARDS['daily_checkin']} 🌿\n"
            f"  💬 Izoh qoldirish — {ECOPOINT_REWARDS['comment']} 🌿"
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="📜 Tarix", callback_data="eco_history")
        builder.button(text="🛒 Do'konga o'tish", callback_data="eco_to_shop")
        builder.button(text="👥 Do'stga ulashish", callback_data=f"eco_share:{uid}")
        builder.adjust(2)
        await msg.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())

    elif role in ("admin", "coordinator"):
        top = await db.get_ecopoint_top(10)
        lines = [
            f"{i+1}. {u['full_name']} — {u['ecopoints']} 🌿"
            for i, u in enumerate(top)
        ] if top else ["Hali EcoPoint yo'q"]
        await msg.answer(
            "🌿 <b>EcoPoint Top 10:</b>\n\n" + "\n".join(lines),
            parse_mode="HTML"
        )


# ── EcoPoint tarixi ────────────────────────────────────────────
@router.callback_query(F.data.startswith("eco_share:"))
async def eco_share_cb(cb: CallbackQuery, bot: Bot):
    uid = int(cb.data.split(":")[1])
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{uid}"
    await cb.message.answer(
        f"👋 <b>Ushbu havolani nusxalang va do'stingizga ulashing</b>\n\n"
        f":\n"
        f"<code>{ref_link}</code>\n\n"
        f"Havola orqali ro'yxatdan o'tgan har bir foydalanuvchi <b>{ECOPOINT_REWARDS['referral']} 🌿 EcoPoint</b> oladi.",
        parse_mode="HTML"
    )
    await cb.answer()


@router.callback_query(F.data == "eco_history")
async def eco_history(cb: CallbackQuery):
    logs = await db.get_ecopoint_log(cb.from_user.id, 15)
    if not logs:
        return await cb.answer("Hali hech qanday EcoPoint harakati yo'q.", show_alert=True)
    lines = []
    for log in logs:
        sign = "+" if log["amount"] > 0 else ""
        lines.append(f"{sign}{log['amount']} 🌿 — {log['reason']} ({log['created_at'][:10]})")
    await cb.message.answer(
        "📜 <b>EcoPoint tarixi (oxirgi 15):</b>\n\n" + "\n".join(lines),
        parse_mode="HTML"
    )
    await cb.answer()


@router.callback_query(F.data == "eco_to_shop")
async def eco_to_shop(cb: CallbackQuery):
    await cb.answer()
    from shop import SHOP_ITEMS
    user = await db.get_user(cb.from_user.id)
    eco = user["ecopoints"] if user else 0
    lines = []
    for item in SHOP_ITEMS:
        status = "✅" if eco >= item["price"] else "🔒"
        lines.append(f"{status} {item['emoji']} {item['name']} — {item['price']} 🌿")
    await cb.message.answer(
        f"🛒 <b>Do'kon</b>\n💰 Sizda: <b>{eco} 🌿 EcoPoint</b>\n\n" + "\n".join(lines) +
        "\n\n🌿 Do'kon tugmasini bosing!",
        parse_mode="HTML"
    )


# ── Admin: EcoPoint bo'limi ───────────────────────────────────
@router.message(F.text == "🌿 EcoPoint Bo'limi")
async def ecopoint_admin_section(msg: Message):
    from handlers_admin import is_admin
    if not is_admin(msg.from_user.id):
        return
    top = await db.get_ecopoint_top(5)
    lines = [f"{i+1}. {u['full_name']} — {u['ecopoints']} 🌿" for i, u in enumerate(top)] if top else ["Hali EcoPoint yo'q"]
    await msg.answer(
        "🌿 <b>EcoPoint Bo'limi</b>\n\nTop 5:\n" + "\n".join(lines),
        parse_mode="HTML",
        reply_markup=kb.ecopoint_admin_menu()
    )


@router.message(F.text == "🌿 EcoPoint Statistika")
async def ecopoint_admin_stats(msg: Message):
    from handlers_admin import is_admin
    if not is_admin(msg.from_user.id):
        return
    top = await db.get_ecopoint_top(20)
    if not top:
        return await msg.answer("Hali EcoPoint yo'q.", reply_markup=kb.ecopoint_admin_menu())
    lines = [f"{i+1}. {u['full_name']} | 🌿 {u['ecopoints']} | 🆔 {u['telegram_id']}" for i, u in enumerate(top)]
    await msg.answer("🌿 <b>EcoPoint Top 20:</b>\n\n" + "\n".join(lines), parse_mode="HTML")


@router.message(F.text == "📜 EcoPoint Tarixi")
async def ecopoint_all_logs(msg: Message):
    from handlers_admin import is_admin
    if not is_admin(msg.from_user.id):
        return
    import aiosqlite as _aio
    async with _aio.connect("challenge_bot.db") as dbc:
        dbc.row_factory = _aio.Row
        async with dbc.execute(
            "SELECT el.*, u.full_name FROM ecopoint_log el "
            "JOIN users u ON el.user_telegram_id = u.telegram_id "
            "ORDER BY el.created_at DESC LIMIT 30"
        ) as cur:
            logs = await cur.fetchall()
    if not logs:
        return await msg.answer("Hali log yo'q.")
    lines = []
    for log in logs:
        sign = "+" if log["amount"] > 0 else ""
        lines.append(f"{log['full_name']}: {sign}{log['amount']} 🌿 — {log['reason']} ({log['created_at'][:10]})")
    await msg.answer("📜 <b>Oxirgi 30 ta harakat:</b>\n\n" + "\n".join(lines), parse_mode="HTML")


@router.message(F.text == "🔙 Orqaga", lambda msg: is_admin(msg.from_user.id))
async def eco_back_to_admin(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Admin panel", reply_markup=kb.main_menu_admin())


# ── Admin: EcoPoint berish ─────────────────────────────────────
@router.message(F.text == "🌿 EcoPoint Berish")
async def admin_give_eco_start(msg: Message, state: FSMContext):
    from handlers_admin import is_admin
    if not is_admin(msg.from_user.id):
        return
    await msg.answer("Foydalanuvchi Telegram ID sini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(AdminEcoStates.user_id)


@router.message(AdminEcoStates.user_id)
async def admin_give_eco_uid(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_admin())
    try:
        uid = int(msg.text)
    except ValueError:
        return await msg.answer("To'g'ri ID kiriting!")
    user = await db.get_user(uid)
    if not user:
        return await msg.answer("Bu ID da foydalanuvchi topilmadi!")
    await state.update_data(target_uid=uid)
    await msg.answer(f"👤 {user['full_name']}\n💰 EcoPoint: {user['ecopoints']}\n\nNecha EcoPoint bermoqchisiz?")
    await state.set_state(AdminEcoStates.amount)


@router.message(AdminEcoStates.amount)
async def admin_give_eco_amount(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_admin())
    try:
        amount = float(msg.text)
    except ValueError:
        return await msg.answer("Son kiriting!")
    await state.update_data(eco_amount=amount)
    await msg.answer("Sabab yozing (masalan: 'Faollik uchun', 'Bonus'):")
    await state.set_state(AdminEcoStates.reason)


@router.message(AdminEcoStates.reason)
async def admin_give_eco_reason(msg: Message, state: FSMContext, bot: Bot):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_admin())
    data = await state.get_data()
    target = data["target_uid"]
    amount = data["eco_amount"]
    reason = msg.text
    await db.add_ecopoints(target, amount, f"Admin: {reason}")
    await state.clear()
    user = await db.get_user(target)
    await msg.answer(
        f"✅ {user['full_name']} ga {amount} 🌿 EcoPoint berildi!\n"
        f"💰 Yangi balans: {user['ecopoints']} 🌿",
        reply_markup=kb.main_menu_admin()
    )
    try:
        await bot.send_message(
            target,
            f"🎁 Sizga <b>{amount} 🌿 EcoPoint</b> berildi!\n"
            f"📝 Sabab: {reason}\n"
            f"💰 Balans: {user['ecopoints']} 🌿",
            parse_mode="HTML"
        )
    except Exception:
        pass


# ── Admin: Missiyaga EcoPoint belgilash ───────────────────────
@router.message(F.text == "🌿 Missiya EcoPoint")
async def mission_eco_start(msg: Message, state: FSMContext):
    from handlers_admin import is_admin
    if not is_admin(msg.from_user.id):
        return
    missions = await db.get_missions()
    if not missions:
        return await msg.answer("Missiyalar yo'q.")
    lines = "\n".join([
        f"#{m['mission_number']} — {m['title']} (🌿 {m['ecopoint_reward'] or 0})"
        for m in missions
    ])
    await msg.answer(f"Missiyalar:\n{lines}\n\nQaysi missiya raqamini o'zgartirmoqchisiz?", reply_markup=kb.cancel_kb())
    await state.set_state(MissionEcoStates.mission_number)


@router.message(MissionEcoStates.mission_number)
async def mission_eco_number(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_admin())
    try:
        mnum = int(msg.text)
    except ValueError:
        return await msg.answer("Son kiriting!")
    mission = await db.get_mission(mnum)
    if not mission:
        return await msg.answer("Topilmadi!")
    await state.update_data(mission_number=mnum)
    await msg.answer(
        f"📌 {mission['title']}\n🌿 Joriy EcoPoint: {mission['ecopoint_reward'] or 0}\n\nYangi EcoPoint miqdorini kiriting:"
    )
    await state.set_state(MissionEcoStates.eco_amount)


@router.message(MissionEcoStates.eco_amount)
async def mission_eco_amount(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_admin())
    try:
        amount = float(msg.text)
    except ValueError:
        return await msg.answer("Son kiriting!")
    data = await state.get_data()
    mnum = data["mission_number"]
    await db.set_mission_ecopoint(mnum, amount)
    await state.clear()
    await msg.answer(
        f"✅ Missiya #{mnum} uchun {amount} 🌿 EcoPoint belgilandi!",
        reply_markup=kb.main_menu_admin()
    )