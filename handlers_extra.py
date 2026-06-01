"""
Qo'shimcha funksiyalar:
  - 📊 Statistika (admin)
  - ⏰ Deadline belgilash (admin)
  - 🏅 Kunlik/Haftalik reyting
  - 💬 Missiya izohi (user)
  - 💬 Izohlarni ko'rish (admin/coordinator)
"""
from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

import database as db
import keyboards as kb
from levels import get_level

router = Router()


class DeadlineStates(StatesGroup):
    mission_number = State()
    deadline_choice = State()
    custom_date = State()

class CommentStates(StatesGroup):
    mission_number = State()
    comment_text = State()

class ViewCommentStates(StatesGroup):
    mission_number = State()


async def get_role(uid: int) -> str:
    from handlers_admin import is_admin
    if is_admin(uid):
        return "admin"
    if await db.get_coordinator(uid):
        return "coordinator"
    if await db.get_inspector(uid):
        return "inspector"
    if await db.get_user(uid):
        return "user"
    return "none"


def deadline_kb():
    kb_b = ReplyKeyboardBuilder()
    kb_b.button(text="⏰ 1 kun")
    kb_b.button(text="⏰ 3 kun")
    kb_b.button(text="⏰ 7 kun")
    kb_b.button(text="📅 O'zim belgilayman")
    kb_b.button(text="❌ Bekor qilish")
    kb_b.adjust(3)
    return kb_b.as_markup(resize_keyboard=True)


def periodic_rating_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Kunlik", callback_data="rating:daily")
    builder.button(text="📆 Haftalik", callback_data="rating:weekly")
    builder.adjust(2)
    return builder.as_markup()


# ── 📊 Statistika ──────────────────────────────────────────────
@router.message(F.text == "📊 Statistika")
async def show_stats(msg: Message):
    uid = msg.from_user.id
    role = await get_role(uid)
    if role not in ("admin", "coordinator"):
        return
    stats = await db.get_stats()
    top = await db.get_top_users(1)
    vip_badge = "👑 " if (top and top[0]['is_vip']) else ""
    top_info = f"{vip_badge}{top[0]['full_name']} ({top[0]['score']} ball)" if top else "—"
    text = (
        "📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Jami ishtirokchilar: <b>{stats['total_users']}</b>\n"
        f"🏘 Guruhlar soni: <b>{stats['total_groups']}</b>\n"
        f"🤝 Coordinatorlar: <b>{stats['total_coordinators']}</b>\n"
        f"🔍 Inspektorlar: <b>{stats['total_inspectors']}</b>\n\n"
        f"📋 Faol missiyalar: <b>{stats['total_missions']}</b>\n"
        f"📤 Jami topshiriqlar: <b>{stats['total_submissions']}</b>\n"
        f"✅ Baholangan: <b>{stats['scored_submissions']}</b>\n"
        f"⏳ Baholanmagan: <b>{stats['total_submissions'] - stats['scored_submissions']}</b>\n\n"
        f"⭐ O'rtacha ball: <b>{stats['avg_score']}</b>\n"
        f"🥇 Lider: <b>{top_info}</b>"
    )
    await msg.answer(text, parse_mode="HTML")


# ── ⏰ Deadline ─────────────────────────────────────────────────
@router.message(F.text == "⏰ Deadline belgilash")
async def deadline_start(msg: Message, state: FSMContext):
    from handlers_admin import is_admin
    if not is_admin(msg.from_user.id):
        return
    await msg.answer("Missiya raqamini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(DeadlineStates.mission_number)


@router.message(DeadlineStates.mission_number)
async def deadline_mission(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_admin())
    try:
        mnum = int(msg.text)
    except ValueError:
        return await msg.answer("Son kiriting!")
    mission = await db.get_mission(mnum)
    if not mission:
        return await msg.answer("Bu raqamli missiya topilmadi!")
    await state.update_data(mission_number=mnum)
    is_open, current_dl = await db.is_mission_open(mnum)
    current_info = f"\n⏰ Joriy deadline: {current_dl}" if current_dl else "\n⏰ Deadline yo'q"
    await msg.answer(
        f"📌 Missiya #{mnum}: {mission['title']}{current_info}\n\nQancha vaqt?",
        reply_markup=deadline_kb()
    )
    await state.set_state(DeadlineStates.deadline_choice)


@router.message(DeadlineStates.deadline_choice)
async def deadline_choice_handler(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_admin())
    data = await state.get_data()
    mnum = data["mission_number"]
    if msg.text == "⏰ 1 kun":
        dl = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    elif msg.text == "⏰ 3 kun":
        dl = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
    elif msg.text == "⏰ 7 kun":
        dl = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    elif msg.text == "📅 O'zim belgilayman":
        await msg.answer("Sana kiriting (KK.OO.YYYY SS:MM):\nMasalan: 25.06.2025 23:59", reply_markup=kb.cancel_kb())
        await state.set_state(DeadlineStates.custom_date)
        return
    else:
        return await msg.answer("Tugmalardan birini tanlang.")
    await db.set_mission_deadline(mnum, dl)
    await state.clear()
    await msg.answer(f"✅ Missiya #{mnum} deadline: {dl}", reply_markup=kb.main_menu_admin())


@router.message(DeadlineStates.custom_date)
async def deadline_custom(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_admin())
    try:
        dt = datetime.strptime(msg.text.strip(), "%d.%m.%Y %H:%M")
        dl = dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return await msg.answer("Noto'g'ri format! KK.OO.YYYY SS:MM\nMasalan: 25.06.2025 23:59")
    data = await state.get_data()
    mnum = data["mission_number"]
    await db.set_mission_deadline(mnum, dl)
    await state.clear()
    await msg.answer(f"✅ Missiya #{mnum} deadline: {msg.text}", reply_markup=kb.main_menu_admin())


# ── 🏅 Davriy reyting ──────────────────────────────────────────
@router.message(F.text == "🏅 Davriy Reyting")
async def periodic_rating_menu(msg: Message):
    role = await get_role(msg.from_user.id)
    if role == "none":
        return
    await msg.answer("Qaysi davrni ko'rmoqchisiz?", reply_markup=periodic_rating_kb())


@router.callback_query(F.data.startswith("rating:"))
async def periodic_rating_show(cb: CallbackQuery):
    period = cb.data.split(":")[1]
    label = "Kunlik 📅" if period == "daily" else "Haftalik 📆"
    top = await db.get_periodic_rating(period, limit=20)
    if not top:
        await cb.message.edit_text(f"🏅 {label} reyting\n\nBu davrda baholangan topshiriq yo'q.")
        return await cb.answer()
    lines = []
    for i, u in enumerate(top):
        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
        vip_badge = "👑 " if u['is_vip'] else ""
        lines.append(f"{medal} {vip_badge}{u['full_name']} | ⭐ {round(u['period_score'], 1)} | 📋 {u['mission_count']} ta")
    await cb.message.edit_text(f"🏅 {label} reyting (Top 20):\n\n" + "\n".join(lines))
    await cb.answer()


# ── 💬 Izoh qoldirish (user) ───────────────────────────────────
@router.message(F.text == "💬 Izoh qoldirish")
async def comment_start(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    role = await get_role(uid)
    if role != "user":
        return
    missions = await db.get_missions()
    if not missions:
        return await msg.answer("Hozircha missiyalar yo'q.")
    mission_list = "\n".join([f"#{m['mission_number']} — {m['title']}" for m in missions])
    await msg.answer(f"Qaysi missiyaga izoh?\n\n{mission_list}\n\nRaqamini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(CommentStates.mission_number)


@router.message(CommentStates.mission_number)
async def comment_mission_number(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_user())
    try:
        mnum = int(msg.text)
    except ValueError:
        return await msg.answer("Son kiriting!")
    mission = await db.get_mission(mnum)
    if not mission:
        return await msg.answer("Topilmadi!")
    await state.update_data(mission_number=mnum)
    await msg.answer(f"📌 #{mnum}: {mission['title']}\n\nIzohingizni yozing:")
    await state.set_state(CommentStates.comment_text)


@router.message(CommentStates.comment_text)
async def comment_save(msg: Message, state: FSMContext, bot: Bot):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_user())
    data = await state.get_data()
    mnum = data["mission_number"]
    uid = msg.from_user.id
    already_commented = await db.has_user_commented(uid, mnum)
    await db.add_comment(uid, mnum, msg.text)
    from ecopoint import ECOPOINT_REWARDS
    reward_text = ""
    if not already_commented:
        await db.add_ecopoints(uid, ECOPOINT_REWARDS["comment"], f"Missiya #{mnum} izoh")
        reward_text = f"\n🌿 +{ECOPOINT_REWARDS['comment']} EcoPoint berildi!"
    await state.clear()
    await msg.answer(
        f"✅ Izohingiz qabul qilindi!{reward_text}",
        reply_markup=kb.main_menu_user()
    )
    user = await db.get_user(uid)
    if user:
        coords = await db.get_group_coordinators(user['group_id'])
        for coord in coords:
            try:
                await bot.send_message(
                    coord['telegram_id'],
                    f"💬 Yangi izoh!\n👤 {user['full_name']} (Guruh #{user['group_id']})\n"
                    f"📌 Missiya #{mnum}\n💭 {msg.text}"
                )
            except Exception:
                pass


# ── 💬 Izohlarni ko'rish (admin/coordinator) ───────────────────
@router.message(F.text == "💬 Izohlarni ko'rish")
async def view_comments_start(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    role = await get_role(uid)
    if role not in ("admin", "coordinator"):
        return
    await msg.answer("Missiya raqamini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(ViewCommentStates.mission_number)


@router.message(ViewCommentStates.mission_number)
async def view_comments_show(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        uid = msg.from_user.id
        role = await get_role(uid)
        rm = kb.main_menu_admin() if role == "admin" else kb.main_menu_coordinator()
        return await msg.answer("Bekor qilindi.", reply_markup=rm)
    try:
        mnum = int(msg.text)
    except ValueError:
        return await msg.answer("Son kiriting!")
    await state.clear()
    comments = await db.get_comments(mnum)
    uid = msg.from_user.id
    role = await get_role(uid)
    rm = kb.main_menu_admin() if role == "admin" else kb.main_menu_coordinator()
    if not comments:
        return await msg.answer(f"Missiya #{mnum} uchun izoh yo'q.", reply_markup=rm)
    text = f"💬 Missiya #{mnum} izohlari (oxirgi 20):\n\n"
    for c in comments:
        text += f"👤 {c['full_name']}\n💭 {c['comment']}\n🕐 {c['created_at']}\n\n"
    await msg.answer(text, reply_markup=rm)