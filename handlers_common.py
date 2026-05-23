"""
Bir xil tugma nomlarini ishlatadigan handlerlar shu yerda markazlashtirilgan.
Router tartibi muammosini hal qiladi.
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import database as db
from levels import get_level
import keyboards as kb
from states import CoordMissionStates, InspectorMissionStates

router = Router()


async def get_role(uid: int):
    """admin | coordinator | inspector | user | None"""
    from handlers_admin import is_admin
    if is_admin(uid):
        return "admin"
    if await db.get_coordinator(uid):
        return "coordinator"
    if await db.get_inspector(uid):
        return "inspector"
    if await db.get_user(uid):
        return "user"
    return None


# ── 👥 Users ──────────────────────────────────────────────────
@router.message(F.text == "👥 Users")
async def users_handler(msg: Message):
    uid = msg.from_user.id
    role = await get_role(uid)

    if role == "admin":
        await msg.answer("Users bo'limi:", reply_markup=kb.users_menu_admin())

    elif role == "coordinator":
        groups = await db.get_coordinator_groups(uid)
        if not groups:
            return await msg.answer("Sizga guruh tayinlanmagan.")
        for gnum in groups:
            users = await db.get_users_by_group(gnum)
            await msg.answer(f"👥 Guruh #{gnum} a'zolari:")
            for u in users:
                text = f"👤 {u['full_name']} | 🆔 {u['telegram_id']} | ⭐ {u['score']}"
                await msg.answer(text, reply_markup=kb.inline_user_score_buttons(u['telegram_id'], "coord"))
        await msg.answer("Menyu", reply_markup=kb.main_menu_coordinator())


# ── 🏆 Reyting ─────────────────────────────────────────────────
@router.message(F.text == "🏆 Reyting")
async def rating_handler(msg: Message):
    uid = msg.from_user.id
    role = await get_role(uid)

    if role in ("admin", "coordinator"):
        top = await db.get_top_users(50)
        if not top:
            return await msg.answer("Reyting bo'sh.")
        lines = [
            f"{i+1}. {'👑 ' if u['is_vip'] else ''}{u['full_name']} | 🆔 {u['telegram_id']} | {get_level(u['score'])} | ⭐ {u['score']}"
            for i, u in enumerate(top)
        ]
        await msg.answer("🏆 Top 50 ishtirokchi:\n\n" + "\n".join(lines))

    elif role == "user":
        top = await db.get_top_users(50)
        if not top:
            return await msg.answer("Reyting bo'sh.")
        lines = [f"{i+1}. {'👑VIP| ' if u['is_vip'] else ''}{u['full_name']} | {get_level(u['score'])} | ⭐ {u['score']}" for i, u in enumerate(top)]
        await msg.answer("🏆 Top 50 ishtirokchi:\n\n" + "\n".join(lines))


# ── 📋 Missialar ───────────────────────────────────────────────
@router.message(F.text == "📋 Missialar")
async def missions_handler(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    role = await get_role(uid)

    if role == "admin":
        await msg.answer("Missialar bo'limi:", reply_markup=kb.missions_menu_admin())

    elif role == "coordinator":
        await msg.answer("Missiya raqamini kiriting:", reply_markup=kb.cancel_kb())
        await state.set_state(CoordMissionStates.mission_number)

    elif role == "inspector":
        await msg.answer("Guruh raqamini kiriting:", reply_markup=kb.cancel_kb())
        await state.set_state(InspectorMissionStates.group_number)

    elif role == "user":
        missions = await db.get_missions()
        if not missions:
            return await msg.answer("Hozircha missiyalar yo'q.")
        for m in missions:
            sub = await db.get_submission(uid, m['mission_number'])
            if sub and sub['final_score'] is not None:
                btn = None
                status = f"\n✅ Baholangan: {sub['final_score']}/10"
            elif sub:
                btn = None
                status = "\n⏳ Tekshirilmoqda..."
            else:
                btn = kb.inline_submit_mission(m['mission_number'])
                status = ""
            text = f"📌 Missiya #{m['mission_number']}: {m['title']}\n{m['description']}{status}"
            if m['file_id']:
                if m['file_type'] == 'photo':
                    await msg.answer_photo(m['file_id'], caption=text, reply_markup=btn)
                elif m['file_type'] == 'video':
                    await msg.answer_video(m['file_id'], caption=text, reply_markup=btn)
                elif m['file_type'] == 'document':
                    await msg.answer_document(m['file_id'], caption=text, reply_markup=btn)
            else:
                await msg.answer(text, reply_markup=btn)