import json
import io
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

import database as db
import keyboards as kb
from states import (
    AddMissionStates, AddCoordinatorStates, AddInspectorStates,
    AssignGroupStates, BroadcastStates, SearchUserStates,
    AdjustScoreStates, GroupSearchStates, MissionArchiveStates,
    AdminScoreMissionStates
)

router = Router()

ADMIN_IDS = []


def set_admin_ids(ids):
    global ADMIN_IDS
    ADMIN_IDS = ids


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ── Main menu ───────────────────────────────────────────────
@router.message(Command("admin"))
async def admin_cmd(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer("Admin panelga xush kelibsiz!", reply_markup=kb.main_menu_admin())

@router.message(F.text == "🔙 Orqaga")
async def back_to_main(msg: Message, state: FSMContext):
    await state.clear()
    uid = msg.from_user.id
    if is_admin(uid):
        await msg.answer("Asosiy menyu", reply_markup=kb.main_menu_admin())
    elif await db.get_coordinator(uid):
        await msg.answer("Asosiy menyu", reply_markup=kb.main_menu_coordinator())
    elif await db.get_inspector(uid):
        await msg.answer("Asosiy menyu", reply_markup=kb.main_menu_inspector())
    else:
        user = await db.get_user(uid)
        if user:
            await msg.answer("Asosiy menyu", reply_markup=kb.main_menu_user())

# Missialar — handlers_common.py da

@router.message(F.text == "➕ Joylash")
async def add_mission_start(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer("Missiya raqamini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(AddMissionStates.number)

@router.message(AddMissionStates.number)
async def add_mission_number(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.missions_menu_admin())
    try:
        num = int(msg.text)
        await state.update_data(number=num)
        await msg.answer("Missiya sarlavhasini kiriting:")
        await state.set_state(AddMissionStates.title)
    except ValueError:
        await msg.answer("Iltimos, son kiriting!")

@router.message(AddMissionStates.title)
async def add_mission_title(msg: Message, state: FSMContext):
    await state.update_data(title=msg.text)
    await msg.answer("Missiya tavsifini kiriting:")
    await state.set_state(AddMissionStates.description)

@router.message(AddMissionStates.description)
async def add_mission_desc(msg: Message, state: FSMContext):
    await state.update_data(description=msg.text)
    await msg.answer("Media fayl yuboring (foto/video/hujjat) yoki /skip yozing:")
    await state.set_state(AddMissionStates.media)

@router.message(AddMissionStates.media)
async def add_mission_media(msg: Message, state: FSMContext):
    data = await state.get_data()
    file_id = None
    file_type = None
    if msg.text and msg.text.lower() == "/skip":
        pass
    elif msg.photo:
        file_id = msg.photo[-1].file_id
        file_type = "photo"
    elif msg.video:
        file_id = msg.video.file_id
        file_type = "video"
    elif msg.document:
        file_id = msg.document.file_id
        file_type = "document"
    await db.add_mission(data["number"], data["title"], data["description"], file_id, file_type)
    await state.clear()
    await msg.answer(f"✅ Missiya #{data['number']} qo'shildi!", reply_markup=kb.missions_menu_admin())

# Delete mission
@router.message(F.text == "🗑 Missiyani o'chirish")
async def delete_mission_list(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    missions = await db.get_missions()
    if not missions:
        return await msg.answer("Missiyalar yo'q.")
    for m in missions:
        text = f"📌 Missiya #{m['mission_number']}\n📝 {m['title']}\n{m['description']}"
        await msg.answer(text, reply_markup=kb.inline_delete_mission(m['mission_number']))

@router.callback_query(F.data.startswith("del_mission:"))
async def delete_mission_cb(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await cb.answer("Ruxsat yo'q!")
    num = int(cb.data.split(":")[1])
    await db.delete_mission(num)
    await cb.message.edit_text(f"🗑 Missiya #{num} o'chirildi.")
    await cb.answer("O'chirildi!")

# Check submissions (admin)
@router.message(F.text == "✅ Tekshirish")
async def admin_check_start(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    subs = await db.get_all_submissions()
    if not subs:
        return await msg.answer("Tekshirilmagan topshiriqlar yo'q.")
    await state.set_state(AdminScoreMissionStates.select_submission)
    for s in subs:
        text = (f"👤 {s['full_name']} (Guruh #{s['group_id']})\n"
                f"📌 Missiya #{s['mission_number']}\n"
                f"📅 {s['submitted_at']}\n")
        await _send_submission_content(msg, s, text)

async def _send_submission_content(msg: Message, s, text: str):
    ikb = kb.inline_quality_score(s['id'])
    if s['file_id']:
        if s['file_type'] == 'photo':
            await msg.answer_photo(s['file_id'], caption=text, reply_markup=ikb)
        elif s['file_type'] == 'video':
            await msg.answer_video(s['file_id'], caption=text, reply_markup=ikb)
        elif s['file_type'] == 'document':
            await msg.answer_document(s['file_id'], caption=text, reply_markup=ikb)
    else:
        if s['content']:
            text += f"\n💬 {s['content']}"
        await msg.answer(text, reply_markup=ikb)

@router.callback_query(F.data.startswith("quality:"))
async def quality_score_cb(cb: CallbackQuery):
    parts = cb.data.split(":")
    sub_id = int(parts[1])
    quality = float(parts[2])
    await cb.message.edit_reply_markup(reply_markup=kb.inline_time_score(sub_id, quality))
    await cb.answer(f"Sifat bali: {quality}")

@router.callback_query(F.data.startswith("time_sc:"))
async def time_score_cb(cb: CallbackQuery, bot: Bot):
    from levels import get_level, get_next_level
    parts = cb.data.split(":")
    sub_id = int(parts[1])
    time_sc = float(parts[2])
    quality = float(parts[3])
    final = (quality + time_sc) / 2
    user_id, old_level, new_level = await db.score_submission(sub_id, quality, time_sc, cb.from_user.id)
    # Get submission info
    async with __import__('aiosqlite').connect("challenge_bot.db") as dbc:
        dbc.row_factory = __import__('aiosqlite').Row
        async with dbc.execute("SELECT * FROM mission_submissions WHERE id=?", (sub_id,)) as cur:
            sub = await cur.fetchone()
    if sub:
        user = await db.get_user(sub['user_telegram_id'])
        # Foydalanuvchiga xabar
        try:
            score_msg = (
                f"✅ Missiya #{sub['mission_number']} baholandi!\n"
                f"⭐ Sifat: {quality}/10\n⏱ Vaqt: {time_sc}/10\n📊 Jami: {final}/10"
            )
            if old_level and new_level:
                score_msg += f"\n\n🎉 Tabriklaymiz! Darajangiz ko'tarildi:\n{old_level} ➜ {new_level}"
            await bot.send_message(sub['user_telegram_id'], score_msg)
        except Exception:
            pass
        # Coordinator xabardor qilish
        if user:
            coords = await db.get_group_coordinators(user['group_id'])
            for coord in coords:
                try:
                    coord_msg = (
                        f"📊 {user['full_name']} — Missiya #{sub['mission_number']} baholandi.\n"
                        f"Sifat: {quality} | Vaqt: {time_sc} | Jami: {final}"
                    )
                    if old_level and new_level:
                        coord_msg += f"\n🏅 Daraja: {old_level} ➜ {new_level}"
                    await bot.send_message(coord['telegram_id'], coord_msg)
                except Exception:
                    pass
    await cb.message.edit_text(
        f"✅ Baholandi! Sifat: {quality} | Vaqt: {time_sc} | Jami: {final}"
    )
    await cb.answer(f"Baholandi! Jami: {final}")

# Users menu — handlers_common.py da

@router.message(F.text == "📋 Ro'yxat")
async def users_list(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    users = await db.get_all_users()
    if not users:
        return await msg.answer("Ro'yxatdan o'tgan foydalanuvchi yo'q.")
    data = [dict(u) for u in users]
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    file = BufferedInputFile(json_bytes, filename="users.json")
    await msg.answer_document(file, caption=f"👥 Jami: {len(data)} ta foydalanuvchi")

@router.message(F.text == "🔍 Qidirish")
async def search_user_start(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer("Foydalanuvchi ismi yoki ID raqamini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(SearchUserStates.query)

@router.message(SearchUserStates.query)
async def search_user(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.users_menu_admin())
    user = await db.find_user(msg.text)
    await state.clear()
    if not user:
        return await msg.answer("Foydalanuvchi topilmadi.", reply_markup=kb.users_menu_admin())
    coords = await db.get_group_coordinators(user['group_id'] or 0)
    coord_info = ", ".join([f"@{c['username'] or c['telegram_id']}" for c in coords]) or "Tayinlanmagan"
    text = (f"👤 {user['full_name']}\n"
            f"🆔 {user['telegram_id']}\n"
            f"📱 {user['phone']}\n"
            f"🏠 {user['address']}\n"
            f"👥 Guruh #{user['group_id']}\n"
            f"🤝 Coordinator: {coord_info}\n"
            f"⭐ Ball: {user['score']}")
    await msg.answer(text, reply_markup=kb.inline_user_score_buttons(user['telegram_id'], "admin"))
    await msg.answer("Asosiy menyu", reply_markup=kb.users_menu_admin())

@router.message(F.text == "👥 Guruhdan qidirish")
async def group_search_start(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer("Guruh raqamini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(GroupSearchStates.group_number)

@router.message(GroupSearchStates.group_number)
async def group_search(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.users_menu_admin())
    try:
        gnum = int(msg.text)
    except ValueError:
        return await msg.answer("Son kiriting!")
    await state.clear()
    coords = await db.get_group_coordinators(gnum)
    users = await db.get_users_by_group(gnum)
    coord_info = "\n".join([f"  🤝 {c['full_name']} (@{c['username'] or c['telegram_id']})" for c in coords]) or "  Tayinlanmagan"
    header = f"👥 Guruh #{gnum}\nCoordinatorlar:\n{coord_info}\n\nA'zolar:"
    await msg.answer(header)
    for u in users:
        text = f"👤 {u['full_name']} | 🆔 {u['telegram_id']} | ⭐ {u['score']}"
        await msg.answer(text, reply_markup=kb.inline_user_score_buttons(u['telegram_id'], "admin"))
    if not users:
        await msg.answer("Bu guruhda foydalanuvchi yo'q.")
    await msg.answer("Menyu", reply_markup=kb.users_menu_admin())

# ── Score adjust callbacks ─────────────────────────────────────
_pending_score_adjust = {}  # chat_id -> (user_id, action)

@router.callback_query(F.data.startswith("add_score:") | F.data.startswith("sub_score:"))
async def score_adjust_cb(cb: CallbackQuery, state: FSMContext):
    parts = cb.data.split(":")
    action = "add" if parts[0] == "add_score" else "sub"
    target_uid = int(parts[1])
    await state.update_data(score_target=target_uid, score_action=action)
    await state.set_state(AdjustScoreStates.delta)
    label = "Qo'shish" if action == "add" else "Ayirish"
    await cb.message.answer(f"{label} uchun ball miqdorini kiriting:")
    await cb.answer()

@router.message(AdjustScoreStates.delta)
async def score_adjust_value(msg: Message, state: FSMContext, bot: Bot):
    try:
        delta = float(msg.text)
    except ValueError:
        return await msg.answer("Son kiriting!")
    data = await state.get_data()
    target = data.get("score_target")
    action = data.get("score_action")
    if action == "sub":
        delta = -delta
    old_level, new_level = await db.update_user_score(target, delta)
    await state.clear()
    action_word = "qo'shildi" if delta > 0 else "ayirildi"
    await msg.answer(f"✅ Ball {action_word}: {abs(delta)}")
    # Foydalanuvchiga daraja o'zgarganda xabar yuborish
    if old_level and new_level and target:
        try:
            await bot.send_message(
                target,
                f"🎉 Tabriklaymiz! Darajangiz ko'tarildi:\n{old_level} ➜ {new_level}"
            )
        except Exception:
            pass

# Reyting — handlers_common.py da

# ── Inspectors ─────────────────────────────────────────────────
@router.message(F.text == "🔍 Inspektorlar")
async def inspectors_menu(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer("Inspektorlar bo'limi:", reply_markup=kb.inspectors_menu_admin())

@router.message(F.text == "➕ Inspektor Tayinlash")
async def add_inspector_start(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer("Inspektorning Telegram ID sini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(AddInspectorStates.telegram_id)

@router.message(AddInspectorStates.telegram_id)
async def add_inspector(msg: Message, state: FSMContext, bot: Bot):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.inspectors_menu_admin())
    try:
        tid = int(msg.text)
    except ValueError:
        return await msg.answer("To'g'ri ID kiriting!")
    try:
        chat = await bot.get_chat(tid)
        fn = chat.full_name or str(tid)
        uname = chat.username or ""
    except Exception:
        fn = str(tid)
        uname = ""
    await db.add_inspector(tid, fn, uname)
    await state.clear()
    await msg.answer(f"✅ {fn} inspektor etib tayinlandi!", reply_markup=kb.inspectors_menu_admin())

@router.message(F.text == "📋 Inspektor Ro'yxat")
async def inspectors_list(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    inspectors = await db.get_inspectors()
    if not inspectors:
        return await msg.answer("Inspektorlar yo'q.")
    for insp in inspectors:
        text = f"🔍 {insp['full_name']}\n🆔 {insp['telegram_id']}\n@{insp['username'] or '—'}"
        await msg.answer(text, reply_markup=kb.inline_delete_inspector(insp['telegram_id']))

@router.callback_query(F.data.startswith("del_insp:"))
async def delete_inspector_cb(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await cb.answer("Ruxsat yo'q!")
    tid = int(cb.data.split(":")[1])
    await db.remove_inspector(tid)
    await cb.message.edit_text("🗑 Inspektor o'chirildi.")
    await cb.answer()

# ── Coordinators ───────────────────────────────────────────────
@router.message(F.text == "🤝 Coordinators")
async def coordinators_menu(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer("Coordinatorlar bo'limi:", reply_markup=kb.coordinators_menu_admin())

@router.message(F.text == "➕ Coordinator Tayinlash")
async def add_coordinator_start(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer("Coordinatorning Telegram ID sini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(AddCoordinatorStates.telegram_id)

@router.message(AddCoordinatorStates.telegram_id)
async def add_coordinator(msg: Message, state: FSMContext, bot: Bot):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.coordinators_menu_admin())
    try:
        tid = int(msg.text)
    except ValueError:
        return await msg.answer("To'g'ri ID kiriting!")
    try:
        chat = await bot.get_chat(tid)
        fn = chat.full_name or str(tid)
        uname = chat.username or ""
    except Exception:
        fn = str(tid)
        uname = ""
    await db.add_coordinator(tid, fn, uname)
    await state.clear()
    await msg.answer(f"✅ {fn} coordinator etib tayinlandi!", reply_markup=kb.coordinators_menu_admin())

@router.message(F.text == "📋 Coordinator Ro'yxat")
async def coordinators_list(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    coords = await db.get_coordinators()
    if not coords:
        return await msg.answer("Coordinatorlar yo'q.")
    for coord in coords:
        groups = await db.get_coordinator_groups(coord['telegram_id'])
        g_text = ", ".join([f"#{g}" for g in groups]) if groups else "Tayinlanmagan"
        text = (f"🤝 {coord['full_name']}\n"
                f"🆔 {coord['telegram_id']}\n"
                f"@{coord['username'] or '—'}\n"
                f"👥 Guruhlar: {g_text}")
        await msg.answer(text, reply_markup=kb.inline_delete_coordinator(coord['telegram_id']))

@router.callback_query(F.data.startswith("del_coord:"))
async def delete_coordinator_cb(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await cb.answer("Ruxsat yo'q!")
    tid = int(cb.data.split(":")[1])
    await db.remove_coordinator(tid)
    await cb.message.edit_text("🗑 Coordinator o'chirildi.")
    await cb.answer()

# ── Assign group ───────────────────────────────────────────────
@router.message(F.text == "👥 Guruhga tayinlash")
async def assign_group_start(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer("Guruh raqamini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(AssignGroupStates.group_number)

@router.message(AssignGroupStates.group_number)
async def assign_group_number(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_admin())
    try:
        gnum = int(msg.text)
    except ValueError:
        return await msg.answer("Son kiriting!")
    await state.update_data(group_number=gnum)
    coords = await db.get_group_coordinators(gnum)
    if coords:
        info = "\n".join([f"  🤝 {c['full_name']} (@{c['username'] or c['telegram_id']})" for c in coords])
        await msg.answer(f"Guruh #{gnum} coordinatorlari:\n{info}\n\nYangi coordinator ID sini kiriting:")
    else:
        await msg.answer(f"Guruh #{gnum} ga coordinator tayinlanmagan.\nCoordinator ID sini kiriting:")
    await state.set_state(AssignGroupStates.coordinator_id)

@router.message(AssignGroupStates.coordinator_id)
async def assign_group_coordinator(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_admin())
    try:
        cid = int(msg.text)
    except ValueError:
        return await msg.answer("To'g'ri ID kiriting!")
    data = await state.get_data()
    gnum = data["group_number"]
    ok, result_msg = await db.assign_coordinator_to_group(gnum, cid)
    await state.clear()
    await msg.answer(result_msg, reply_markup=kb.main_menu_admin())

# ── Broadcast ──────────────────────────────────────────────────
@router.message(F.text == "📢 Hammaga habar")
async def broadcast_start(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer("Yubormoqchi bo'lgan xabarni yuboring (matn, rasm, video yoki fayl):", reply_markup=kb.cancel_kb())
    await state.set_state(BroadcastStates.content)

@router.message(BroadcastStates.content)
async def broadcast_send(msg: Message, state: FSMContext, bot: Bot):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_admin())
    users = await db.get_all_users()
    count = 0
    for u in users:
        try:
            if msg.photo:
                await bot.send_photo(u['telegram_id'], msg.photo[-1].file_id, caption=msg.caption or "")
            elif msg.video:
                await bot.send_video(u['telegram_id'], msg.video.file_id, caption=msg.caption or "")
            elif msg.document:
                await bot.send_document(u['telegram_id'], msg.document.file_id, caption=msg.caption or "")
            elif msg.text:
                await bot.send_message(u['telegram_id'], msg.text)
            count += 1
        except Exception:
            pass
    await state.clear()
    await msg.answer(f"✅ {count} ta foydalanuvchiga yuborildi.", reply_markup=kb.main_menu_admin())

# ── Archive missions ───────────────────────────────────────────
@router.message(F.text == "📁 Arxiv Missialar")
async def archive_start(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    if not (is_admin(uid) or await db.get_coordinator(uid)):
        return
    await msg.answer("Missiya raqamini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(MissionArchiveStates.mission_number)

@router.message(MissionArchiveStates.mission_number)
async def archive_mission_number(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        uid = msg.from_user.id
        rm = kb.main_menu_admin() if is_admin(uid) else kb.main_menu_coordinator()
        return await msg.answer("Bekor qilindi.", reply_markup=rm)
    try:
        mnum = int(msg.text)
        await state.update_data(mission_number=mnum)
        await msg.answer("Guruh raqamini kiriting (0 = barcha guruhlar):")
        await state.set_state(MissionArchiveStates.group_number)
    except ValueError:
        await msg.answer("Son kiriting!")

@router.message(MissionArchiveStates.group_number)
async def archive_show(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.")
    try:
        gnum = int(msg.text)
    except ValueError:
        return await msg.answer("Son kiriting!")
    data = await state.get_data()
    mnum = data["mission_number"]
    await state.clear()
    subs = await db.get_scored_submissions(mnum, gnum if gnum != 0 else None)
    uid = msg.from_user.id
    rm = kb.main_menu_admin() if is_admin(uid) else kb.main_menu_coordinator()
    if not subs:
        return await msg.answer("Bu mezonlarga mos arxiv yo'q.", reply_markup=rm)
    for s in subs:
        text = (f"👤 {s['full_name']} (Guruh #{s['group_id']})\n"
                f"📌 Missiya #{s['mission_number']}\n"
                f"⭐ Sifat: {s['quality_score']} | Vaqt: {s['time_score']} | Jami: {s['final_score']}\n"
                f"📅 {s['submitted_at']}")
        await msg.answer(text, reply_markup=kb.inline_archive_score(s['id']))
    await msg.answer("Menyu", reply_markup=rm)

@router.callback_query(F.data.startswith("arch_add:") | F.data.startswith("arch_sub:"))
async def archive_score_adjust(cb: CallbackQuery, state: FSMContext):
    parts = cb.data.split(":")
    action = "add" if parts[0] == "arch_add" else "sub"
    sub_id = int(parts[1])
    await state.update_data(arch_sub_id=sub_id, arch_action=action)
    await state.set_state(AdjustScoreStates.delta)
    label = "Qo'shish" if action == "add" else "Ayirish"
    await cb.message.answer(f"{label} uchun ball miqdorini kiriting:")
    await cb.answer()