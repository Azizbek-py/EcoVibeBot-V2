"""
Bir xil tugma nomlarini ishlatadigan handlerlar — rol bo'yicha ajratiladi.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

import database as db
from subscription import subscription_guard
from levels import get_level
import keyboards as kb
from states import CoordMissionStates, InspectorMissionStates, UserMissionStates

router = Router()


async def get_role(uid: int) -> str:
    from handlers_admin import is_admin
    if is_admin(uid): return "admin"
    if await db.get_coordinator(uid): return "coordinator"
    if await db.get_inspector(uid): return "inspector"
    if await db.get_user(uid): return "user"
    return "none"


# ── 🔙 Orqaga — BIRINCHI, barcha holatlarda ishlaydi ──────────
@router.message(F.text == "🔙 Orqaga")
async def back_handler(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    await state.clear()
    role = await get_role(uid)
    if role == "admin":
        from handlers_admin import is_admin
        await msg.answer("Asosiy menyu", reply_markup=kb.main_menu_admin())
    elif role == "coordinator":
        await msg.answer("Asosiy menyu", reply_markup=kb.main_menu_coordinator())
    elif role == "inspector":
        await msg.answer("Asosiy menyu", reply_markup=kb.main_menu_inspector())
    elif role == "user":
        await msg.answer("Asosiy menyu", reply_markup=kb.main_menu_user())


# Global cancel button — clear any state and return to role main menu
@router.message(F.text == "❌ Bekor qilish")
async def cancel_handler(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    await state.clear()
    role = await get_role(uid)
    if role == "admin":
        await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_admin())
    elif role == "coordinator":
        await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_coordinator())
    elif role == "inspector":
        await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_inspector())
    elif role == "user":
        await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_user())
    else:
        await msg.answer("Bekor qilindi.")


# ── 👥 Users ───────────────────────────────────────────────────
@router.message(F.text == "👥 Users")
async def users_handler(msg: Message, bot: Bot):
    uid = msg.from_user.id
    if not await subscription_guard(msg, bot):
        return
    role = await get_role(uid)
    if role == "inspector":
        return
    if role == "admin":
        await msg.answer("Users bo'limi:", reply_markup=kb.users_menu_admin())
    elif role == "coordinator":
        groups = await db.get_coordinator_groups(uid)
        if not groups:
            return await msg.answer("Sizga guruh tayinlanmagan.")
        await msg.answer("Users bo'limi:", reply_markup=kb.coord_users_menu())


# ── 🏆 Reyting ─────────────────────────────────────────────────
@router.message(F.text == "🏆 Reyting")
async def rating_handler(msg: Message, bot: Bot):
    uid = msg.from_user.id
    if not await subscription_guard(msg, bot):
        return
    role = await get_role(uid)
    top = await db.get_top_users(50)
    if not top:
        return await msg.answer("Reyting bo'sh.")
    medals = ["🥇", "🥈", "🥉"]
    if role in ("admin", "coordinator"):
        lines = [
            f"{medals[i] if i < 3 else f'{i+1}.'} {'👑 ' if u['is_vip'] else ''}{u['full_name']} | "
            f"🆔 {u['telegram_id']} | {get_level(u['score'])} | ⭐ {u['score']}"
            for i, u in enumerate(top)
        ]
    else:
        lines = [
            f"{medals[i] if i < 3 else f'{i+1}.'} {'👑 ' if u['is_vip'] else ''}{u['full_name']} | "
            f"{get_level(u['score'])} | ⭐ {u['score']}"
            for i, u in enumerate(top)
        ]
    await msg.answer("🏆 Top 50 ishtirokchi:\n\n" + "\n".join(lines))


# ── 📋 Missialar ───────────────────────────────────────────────
@router.message(F.text == "📋 Missialar")
async def missions_handler(msg: Message, state: FSMContext, bot: Bot):
    uid = msg.from_user.id
    if not await subscription_guard(msg, bot):
        return
    role = await get_role(uid)
    if role == "inspector":
        return
    if role == "admin":
        await msg.answer("Missialar bo'limi:", reply_markup=kb.missions_menu_admin())
    elif role == "coordinator":
        await msg.answer("📋 Missiyalar bo'limi:", reply_markup=kb.missions_menu_coordinator())
        await state.set_state(CoordMissionStates.choose)
    elif role == "user":
        await state.set_state(UserMissionStates.choosing)
        await msg.answer(
            "📋 <b>Missiyalar</b>\n\nQaysi bo'limni ko'rmoqchisiz?",
            parse_mode="HTML",
            reply_markup=kb.missions_menu_user()
        )


# ── Coordinator missiya bo'limi ─────────────────────────────────
@router.message(StateFilter(CoordMissionStates.choose))
async def coord_mission_category(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    text = msg.text
    if text == "🔙 Orqaga":
        await state.clear()
        return await msg.answer("Asosiy menyu", reply_markup=kb.main_menu_coordinator())

    groups = await db.get_coordinator_groups(uid)
    if not groups:
        await state.clear()
        return await msg.answer("Sizga guruh tayinlanmagan.", reply_markup=kb.main_menu_coordinator())

    if text == "📌 Asosiy Missiyalar":
        pending = await db.get_unscored_submissions_for_coordinator_by_type(uid, "main")
        label = "📌 <b>Asosiy Missiyalar</b>"
        mission_type = "main"
    elif text == "⭐ Bonus Missiyalar":
        pending = await db.get_unscored_submissions_for_coordinator_by_type(uid, "bonus")
        label = "⭐ <b>Bonus Missiyalar</b>"
        mission_type = "bonus"
    elif text == "📁 Arxiv Missiyalar":
        scored = await db.get_scored_submissions_for_coordinator(uid)
        label = "📁 <b>Arxiv Missiyalar</b>"
        mission_type = "archive"
    else:
        return await msg.answer("Tugmalardan birini tanlang.", reply_markup=kb.missions_menu_coordinator())

    if text in ("📌 Asosiy Missiyalar", "⭐ Bonus Missiyalar"):
        if not pending:
            await state.clear()
            return await msg.answer("Hozircha baholanmagan missiyalar yo'q.", reply_markup=kb.main_menu_coordinator())
        await msg.answer(label, parse_mode="HTML")
        counts = {}
        for sub in pending:
            counts[sub['mission_number']] = counts.get(sub['mission_number'], 0) + 1
        for mission_number, count in sorted(counts.items()):
            mission = await db.get_mission(mission_number)
            if not mission:
                continue
            mission = dict(mission)
            mission_text = (
                f"📌 Missiya #{mission_number}: {mission['title']}\n"
                f"{mission['description']}\n"
                f"🧾 {count} ta baholanmagan topshiriq\n"
                f"🌿 EcoPoint: {mission.get('ecopoint_reward', 0)}"
            )
            await msg.answer(mission_text, reply_markup=kb.inline_verify_mission(mission_number, mission_type))
    else:
        if not scored:
            await state.clear()
            return await msg.answer("Hozircha baholangan missiyalar yo'q.", reply_markup=kb.main_menu_coordinator())
        await msg.answer(label, parse_mode="HTML")
        counts = {}
        for sub in scored:
            counts[sub['mission_number']] = counts.get(sub['mission_number'], 0) + 1
        for mission_number, count in sorted(counts.items()):
            mission = await db.get_mission(mission_number)
            if not mission:
                continue
            mission = dict(mission)
            mission_text = (
                f"📌 Missiya #{mission_number}: {mission['title']}\n"
                f"{mission['description']}\n"
                f"✅ {count} ta baholangan topshiriq\n"
                f"🌿 EcoPoint: {mission.get('ecopoint_reward', 0)}"
            )
            await msg.answer(mission_text, reply_markup=kb.inline_verify_mission(mission_number, mission_type))

    await state.clear()


# ── User missiya bo'limlari ────────────────────────────────────
async def _send_mission_card(msg: Message, m: dict, uid: int):
    """Faqat topshirilmagan missiyalarni ko'rsatadi."""
    sub = await db.get_submission(uid, m["mission_number"])
    if sub and sub["final_score"] is not None:
        return  # Baholangan — ko'rsatma
    eco_reward = m.get("ecopoint_reward") or 0
    eco_info = f"\n🌿 EcoPoint: {eco_reward}" if eco_reward else ""
    mtype = m.get("mission_type") or "main"
    prefix = "⭐ " if mtype == "bonus" else "📌 "
    if sub:
        btn = None
        status = "\n⏳ Tekshirilmoqda..."
    else:
        btn = kb.inline_submit_mission(m["mission_number"])
        status = ""
    text = f"{prefix}Missiya #{m['mission_number']}: {m['title']}\n{m['description']}{eco_info}{status}"
    file_id = m.get("file_id")
    file_type = m.get("file_type")
    if file_id and file_type == "photo":
        await msg.answer_photo(file_id, caption=text, reply_markup=btn)
    elif file_id and file_type == "video":
        await msg.answer_video(file_id, caption=text, reply_markup=btn)
    elif file_id and file_type == "document":
        await msg.answer_document(file_id, caption=text, reply_markup=btn)
    else:
        await msg.answer(text, reply_markup=btn)


@router.message(StateFilter(UserMissionStates.choosing))
async def user_mission_choice(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    text = msg.text

    if text == "🔙 Orqaga":
        await state.clear()
        return await msg.answer("Asosiy menyu", reply_markup=kb.main_menu_user())

    elif text == "📌 Asosiy Missiyalar":
        missions = await db.get_missions()
        main = [dict(m) for m in missions if (dict(m).get("mission_type") or "main") == "main"]
        if not main:
            return await msg.answer("Hozircha asosiy missiyalar yo'q.")
        await msg.answer("📌 <b>Asosiy Missiyalar</b>", parse_mode="HTML")
        shown = 0
        for m in main:
            await _send_mission_card(msg, m, uid)
            shown += 1
        if shown == 0:
            await msg.answer("Barcha asosiy missiyalar bajarilgan! ✅")

    elif text == "⭐ Bonus Missiyalar":
        missions = await db.get_missions()
        bonus = [dict(m) for m in missions if (dict(m).get("mission_type") or "main") == "bonus"]
        if not bonus:
            return await msg.answer("Hozircha bonus missiyalar yo'q.")
        await msg.answer("⭐ <b>Bonus Missiyalar</b>", parse_mode="HTML")
        shown = 0
        for m in bonus:
            await _send_mission_card(msg, m, uid)
            shown += 1
        if shown == 0:
            await msg.answer("Barcha bonus missiyalar bajarilgan! ✅")

    elif text == "📜 Tarix":
        from datetime import timezone, timedelta, datetime
        TZ_UZ = timezone(timedelta(hours=5))
        import aiosqlite as _aio
        async with _aio.connect("challenge_bot.db") as dbc:
            dbc.row_factory = _aio.Row
            async with dbc.execute(
                "SELECT ms.*, m.title as mission_title FROM mission_submissions ms "
                "LEFT JOIN missions m ON ms.mission_number = m.mission_number "
                "WHERE ms.user_telegram_id = ? ORDER BY ms.submitted_at DESC",
                (uid,)
            ) as cur:
                subs = await cur.fetchall()
        if not subs:
            return await msg.answer(
                "Siz hali hech qanday missiya topshirmagansiz.",
                reply_markup=kb.missions_menu_user()
            )
        await msg.answer("📜 <b>Missiyalar tarixi</b>", parse_mode="HTML")
        for s in subs:
            s = dict(s)
            if s["final_score"] is not None:
                status = (f"✅ Ball: {s['final_score']}/10  "
                          f"(Sifat: {s['quality_score']} | Vaqt: {s['time_score']})")
            else:
                status = "⏳ Tekshirilmoqda..."
            title = s.get("mission_title") or f"Missiya #{s['mission_number']}"
            raw = str(s["submitted_at"])[:16]
            try:
                dt = datetime.strptime(raw, "%Y-%m-%d %H:%M")
                dt_uz = dt.replace(tzinfo=timezone.utc).astimezone(TZ_UZ)
                time_str = dt_uz.strftime("%d.%m.%Y %H:%M")
            except Exception:
                time_str = raw
            await msg.answer(
                f"📌 #{s['mission_number']}: {title}\n"
                f"📅 {time_str}\n"
                f"{status}"
            )

    else:
        await msg.answer("Tugmalardan birini tanlang.", reply_markup=kb.missions_menu_user())