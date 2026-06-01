from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
import json

import database as db
import keyboards as kb
from states import InspectorMainMenuStates, InspectorMissionsStates, InspectorUsersStates, InspectorEventsStates

router = Router()


async def is_inspector(telegram_id: int) -> bool:
    return bool(await db.get_inspector(telegram_id))


# ═══════════════════════════════════════════════════════════════
# MAIN MENU
# ═══════════════════════════════════════════════════════════════

@router.message(F.text == "📋 Inspektor Missiyalar")
async def insp_missions_start(msg: Message):
    uid = msg.from_user.id
    is_insp = await is_inspector(uid)
    if not is_insp:
        return await msg.answer(f"⚠️ Inspektor sifatida qayd qilinmaganiz.\nID: {uid}\n\nAdmin bu ID ni inspektora qo'shishi kerak.")
    await msg.answer("Missiya turini tanlang:", reply_markup=kb.missions_category_kb())


@router.message(F.text == "👥 Inspektor Users")
async def insp_users_start(msg: Message):
    uid = msg.from_user.id
    is_insp = await is_inspector(uid)
    if not is_insp:
        return await msg.answer(f"⚠️ Inspektor sifatida qayd qilinmaganiz.\nID: {uid}")
    # Show users submenu: Ro'yxat / Qidirish / Guruhlar
    await msg.answer("Inspektor Users bo'limi:", reply_markup=kb.users_submenu_kb())


@router.message(F.text == "🏕 Inspektor Tadbirlar")
async def insp_events_start(msg: Message):
    uid = msg.from_user.id
    if not await is_inspector(uid):
        return
    events = await db.get_events()
    if not events:
        return await msg.answer("Tadbir yo'q.", reply_markup=kb.main_menu_inspector())
    for event in events:
        text = (f"🏕 {event['title']}\n"
                f"🔢 #{event['event_number']}\n"
                f"📝 {event['description']}\n"
                f"🏆 Ball: {event['ball_reward']} | 🌿 Eco: {event['eco_reward']}")
        await msg.answer(text, reply_markup=kb.event_check_button(event['event_number']))
    await msg.answer("Tekshirishni tugatdik.", reply_markup=kb.main_menu_inspector())


@router.message(F.text == "💾 Saqlanganlar")
async def insp_saved_items_show(msg: Message):
    uid = msg.from_user.id
    if not await is_inspector(uid):
        return
    items = await db.get_inspector_saved_items(uid)
    if not items:
        return await msg.answer("Saqlangan habar yo'q.", reply_markup=kb.main_menu_inspector())
    for item in items:
        data = json.loads(item['content_json'])
        text = f"📌 Turi: {item['message_type']}\n{data.get('text', '')}\n\n🕐 {item['saved_at']}"
        await msg.answer(text, reply_markup=kb.delete_saved_item_button(item['id']))
    await msg.answer("Tugadi.", reply_markup=kb.main_menu_inspector())


# ═══════════════════════════════════════════════════════════════
# MISSIONS SECTION
# ═══════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("insp_mission_cat:"))
async def insp_mission_category(cb: CallbackQuery):
    uid = cb.from_user.id
    if not await is_inspector(uid):
        return await cb.answer("Ruxsat yo'q!", show_alert=True)

    category = cb.data.split(":")[1]
    missions = await db.get_missions(active_only=True)
    missions = [m for m in missions if (m['mission_type'] if 'mission_type' in m.keys() else 'main') == category]

    if not missions:
        await cb.message.edit_text(f"Bu kategoriyada missiya yo'q.", reply_markup=kb.main_menu_inspector())
        return await cb.answer()

    text = f"{'📌 Asosiy' if category == 'main' else '⭐ Bonus'} Missiyalar:\n\n"
    for mission in missions:
        text += f"#{mission['mission_number']} - {mission['title']}\n"

    await cb.message.edit_text(text)
    for mission in missions:
        m_text = (f"#{mission['mission_number']} - {mission['title']}\n"
                  f"📝 {mission['description']}")
        await cb.message.answer(m_text, reply_markup=kb.mission_check_button(mission['mission_number']))
    await cb.message.answer("Tekshiringni tugatdik.", reply_markup=kb.main_menu_inspector())
    await cb.answer()


@router.callback_query(F.data.startswith("insp_mission_check:"))
async def insp_mission_check(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    if not await is_inspector(uid):
        return await cb.answer("Ruxsat yo'q!", show_alert=True)

    mission_num = int(cb.data.split(":")[1])
    await state.update_data(mission_number=mission_num)
    await cb.message.answer("Guruh raqamini kiriting:")
    await state.set_state(InspectorMissionsStates.group_number)
    await cb.answer()


@router.message(InspectorMissionsStates.group_number)
async def insp_mission_show_group(msg: Message, state: FSMContext):
    try:
        group_num = int(msg.text)
    except ValueError:
        return await msg.answer("Son kiriting!")

    data = await state.get_data()
    mission_num = data['mission_number']
    await state.clear()

    subs = await db.get_submissions_for_mission(mission_num, group_num)
    subs = [s for s in subs if s['final_score'] is not None]  # Only rated

    if not subs:
        return await msg.answer("Bu guruhda ushbu missiya uchun baholangan topshiriq yo'q.",
                              reply_markup=kb.main_menu_inspector())

    for s in subs:
        coords = await db.get_group_coordinators(group_num)
        coord_name = coords[0]['full_name'] if coords else "Tayinlanmagan"
        vip_badge = "👑 " if s['is_vip'] else ""
        text = (f"👤 {vip_badge}{s['full_name']}\n"
                f"🆔 {s['user_telegram_id']}\n"
                f"📌 Missiya #{s['mission_number']}\n"
                f"👥 Guruh #{group_num}\n"
                f"🤝 Coordinator: {coord_name}\n"
                f"⭐ Ball: {s['final_score']}")

        if s['file_id']:
            if s['file_type'] == 'photo':
                await msg.answer_photo(s['file_id'], caption=text,
                                     reply_markup=kb.save_message_button('mission_submission', f"{s['id']}:{group_num}"))
            elif s['file_type'] == 'video':
                await msg.answer_video(s['file_id'], caption=text,
                                     reply_markup=kb.save_message_button('mission_submission', f"{s['id']}:{group_num}"))
            elif s['file_type'] == 'document':
                await msg.answer_document(s['file_id'], caption=text,
                                        reply_markup=kb.save_message_button('mission_submission', f"{s['id']}:{group_num}"))
        else:
            if s['content']:
                text += f"\n💬 {s['content']}"
            await msg.answer(text, reply_markup=kb.save_message_button('mission_submission', f"{s['id']}:{group_num}"))

    await msg.answer("Tekshirish tugadi.", reply_markup=kb.main_menu_inspector())


# ═══════════════════════════════════════════════════════════════
# USERS SECTION
# ═══════════════════════════════════════════════════════════════

@router.callback_query(F.data == "insp_users_list")
async def insp_users_list(cb: CallbackQuery):
    uid = cb.from_user.id
    if not await is_inspector(uid):
        return await cb.answer("Ruxsat yo'q!", show_alert=True)

    users = await db.get_all_users()
    users_data = []
    for u in users:
        users_data.append({
            "id": u['id'],
            "telegram_id": u['telegram_id'],
            "full_name": u['full_name'],
            "group_id": u['group_id'],
            "score": u['score'],
            "ecopoints": u['ecopoints'] if 'ecopoints' in u.keys() and u['ecopoints'] is not None else 0
        })

    await cb.message.edit_text(f"```json\n{json.dumps(users_data, indent=2, ensure_ascii=False)}\n```",
                              parse_mode="MarkdownV2")
    await cb.answer()


@router.callback_query(F.data == "insp_users_search")
async def insp_users_search_start(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    if not await is_inspector(uid):
        return await cb.answer("Ruxsat yo'q!", show_alert=True)

    await cb.message.answer("Userning ismini yoki ID raqamini kiriting:")
    await state.set_state(InspectorUsersStates.search_query)
    await cb.answer()


@router.message(InspectorUsersStates.search_query)
async def insp_users_search_process(msg: Message, state: FSMContext):
    query = msg.text.strip()
    await state.clear()

    user = await db.find_user(query)
    if not user:
        return await msg.answer("User topilmadi.", reply_markup=kb.main_menu_inspector())

    vip_badge = "👑 " if user['is_vip'] else ""
    text = (f"👤 {vip_badge}{user['full_name']}\n"
            f"🆔 {user['telegram_id']}\n"
            f"👥 Guruh: #{user['group_id']}\n"
            f"⭐ Ball: {user['score']}\n"
            f"🌿 EcoPoint: {user['ecopoints'] if 'ecopoints' in user.keys() and user['ecopoints'] is not None else 0}")
    await msg.answer(text, reply_markup=kb.info_button(user['telegram_id']))
    await msg.answer("Qidirish tugadi.", reply_markup=kb.main_menu_inspector())


@router.callback_query(F.data.startswith("insp_user_info:"))
async def insp_user_info(cb: CallbackQuery):
    uid = cb.from_user.id
    if not await is_inspector(uid):
        return await cb.answer("Ruxsat yo'q!", show_alert=True)

    user_id = int(cb.data.split(":")[1])
    user = await db.get_user(user_id)
    if not user:
        await cb.message.edit_text("User topilmadi.")
        return await cb.answer()

    # Get score history from scored submissions
    subs = await db.get_scored_submissions()
    score_history = [s for s in subs if s['user_telegram_id'] == user_id]

    text = (f"👤 {user['full_name']}\n"
            f"🆔 {user['telegram_id']}\n"
            f"👥 Guruh: #{user['group_id']}\n"
            f"⭐ Jami Ball: {user['score']}\n"
            f"🌿 Jami EcoPoint: {user['ecopoints'] if 'ecopoints' in user.keys() and user['ecopoints'] is not None else 0}\n\n"
            f"📊 Score Tarixi:\n")

    for s in score_history[-10:]:
        text += f"  • Missiya #{s['mission_number']}: {s['final_score']} ball\n"

    # Get ecopoint history
    eco_log = await db.get_ecopoint_log(user_id, limit=10)
    if eco_log:
        text += f"\n🌿 EcoPoint Tarixi:\n"
        for log in eco_log:
            text += f"  • {log['amount']} - {log['reason']}\n"

    await cb.message.edit_text(text)
    await cb.answer()


@router.callback_query(F.data == "insp_users_groups")
async def insp_users_groups(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    if not await is_inspector(uid):
        return await cb.answer("Ruxsat yo'q!", show_alert=True)

    groups = await db.get_all_groups()
    text = f"Jami guruhlar: {len(groups)}\n\n"

    for g in groups:
        coords = await db.get_group_coordinators(g['group_number'])
        coord_names = ", ".join([c['full_name'] for c in coords]) or "Tayinlanmagan"
        text += f"Guruh #{g['group_number']}: {coord_names}\n"

    await cb.message.edit_text(text)
    await cb.message.answer("Guruh raqamini kiriting:")
    await state.set_state(InspectorUsersStates.group_number)
    await cb.answer()


@router.message(InspectorUsersStates.group_number)
async def insp_users_show_group(msg: Message, state: FSMContext):
    try:
        group_num = int(msg.text)
    except ValueError:
        return await msg.answer("Son kiriting!")

    await state.clear()
    users = await db.get_users_by_group(group_num)

    if not users:
        return await msg.answer("Bu guruhda user yo'q.", reply_markup=kb.main_menu_inspector())

    for u in users:
        vip_badge = "👑 " if u['is_vip'] else ""
        text = f"👤 {vip_badge}{u['full_name']}\n🆔 {u['telegram_id']}\n⭐ Ball: {u['score']}"
        await msg.answer(text, reply_markup=kb.info_button(u['telegram_id']))

    await msg.answer("Guruhdagi userlar.", reply_markup=kb.main_menu_inspector())


# ═══════════════════════════════════════════════════════════════
# EVENTS SECTION
# ═══════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("insp_event_check:"))
async def insp_event_check(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    if not await is_inspector(uid):
        return await cb.answer("Ruxsat yo'q!", show_alert=True)

    event_num = int(cb.data.split(":")[1])
    await state.update_data(event_number=event_num)
    await cb.message.answer("Guruh raqamini kiriting:")
    await state.set_state(InspectorEventsStates.group_number)
    await cb.answer()


@router.message(InspectorEventsStates.group_number)
async def insp_event_show_group(msg: Message, state: FSMContext):
    try:
        group_num = int(msg.text)
    except ValueError:
        return await msg.answer("Son kiriting!")

    data = await state.get_data()
    event_num = data['event_number']
    await state.clear()

    subs = await db.get_event_submissions(event_num, group_num)
    subs = [s for s in subs if s['status'] in ['approved', 'rejected']]  # Only approved/rejected

    if not subs:
        return await msg.answer("Bu guruhda ushbu tadbir uchun tasdiqlangan yoki rad etilgan topshiriq yo'q.",
                              reply_markup=kb.main_menu_inspector())

    event = await db.get_event(event_num)
    coords = await db.get_group_coordinators(group_num)
    coord_name = coords[0]['full_name'] if coords else "Tayinlanmagan"

    for s in subs:
        status_emoji = "✅" if s['status'] == 'approved' else "❌"
        submitted_at = s['submitted_at'] if 'submitted_at' in s.keys() and s['submitted_at'] is not None else "Noma'lum"
        vip_badge = "👑 " if s['is_vip'] else ""
        text = (f"👤 {vip_badge}{s['full_name']}\n"
                f"🆔 {s['user_telegram_id']}\n"
                f"📅 Yuborilgan: {submitted_at}\n"
                f"{status_emoji} Holati: {'Tasdiqlandi' if s['status'] == 'approved' else 'Rad etildi'}\n"
                f"🤝 Coordinator: {coord_name}")

        if s['photo_file_id']:
            await msg.answer_photo(s['photo_file_id'], caption=text,
                                 reply_markup=kb.save_message_button('event_submission', f"{s['id']}:{group_num}"))
        else:
            await msg.answer(text, reply_markup=kb.save_message_button('event_submission', f"{s['id']}:{group_num}"))

    await msg.answer("Tadbir tekshiruvchisi tugadi.", reply_markup=kb.main_menu_inspector())


# ═══════════════════════════════════════════════════════════════
# SAVE/DELETE HANDLERS
# ═══════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("insp_save:"))
async def insp_save_message(cb: CallbackQuery):
    uid = cb.from_user.id
    if not await is_inspector(uid):
        return await cb.answer("Ruxsat yo'q!", show_alert=True)

    parts = cb.data.split(":")
    message_type = parts[1]
    context_id = ":".join(parts[2:])

    content_json = json.dumps({
        "text": cb.message.text or cb.message.caption or "Rasm/Video",
        "message_id": cb.message.message_id,
        "type": message_type
    })

    await db.save_inspector_item(uid, message_type, content_json, context_id)
    await cb.answer("✅ Saqlandi!", show_alert=True)


@router.callback_query(F.data.startswith("insp_delete:"))
async def insp_delete_saved_item(cb: CallbackQuery):
    uid = cb.from_user.id
    if not await is_inspector(uid):
        return await cb.answer("Ruxsat yo'q!", show_alert=True)

    item_id = int(cb.data.split(":")[1])
    await db.delete_inspector_saved_item(item_id, uid)
    await cb.message.edit_text("🗑 O'chirildi.")
    await cb.answer()
