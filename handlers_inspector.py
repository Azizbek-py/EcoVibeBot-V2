from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import database as db
import keyboards as kb
from states import InspectorMissionStates

router = Router()


async def is_inspector(telegram_id: int) -> bool:
    return bool(await db.get_inspector(telegram_id))


@router.message(F.text == "📋 Missialar")
async def insp_missions_start(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    if not await is_inspector(uid):
        return
    await msg.answer("Guruh raqamini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(InspectorMissionStates.group_number)


@router.message(InspectorMissionStates.group_number)
async def insp_group_number(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_inspector())
    try:
        gnum = int(msg.text)
        await state.update_data(group_number=gnum)
        await msg.answer("Missiya raqamini kiriting:")
        await state.set_state(InspectorMissionStates.mission_number)
    except ValueError:
        await msg.answer("Son kiriting!")


@router.message(InspectorMissionStates.mission_number)
async def insp_mission_show(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_inspector())
    try:
        mnum = int(msg.text)
    except ValueError:
        return await msg.answer("Son kiriting!")
    data = await state.get_data()
    gnum = data["group_number"]
    await state.clear()

    coords = await db.get_group_coordinators(gnum)
    coord_info = "\n".join([f"  🤝 {c['full_name']} (@{c['username'] or c['telegram_id']})" for c in coords]) or "  Tayinlanmagan"
    await msg.answer(f"👥 Guruh #{gnum} coordinatorlari:\n{coord_info}")

    subs = await db.get_submissions_for_mission(mnum, gnum)
    if not subs:
        return await msg.answer("Bu guruhda ushbu missiya uchun topshiriq yo'q.", reply_markup=kb.main_menu_inspector())

    for s in subs:
        text = (f"👤 {s['full_name']}\n"
                f"🆔 {s['user_telegram_id']}\n"
                f"📌 Missiya #{s['mission_number']}\n"
                f"📅 Yuborilgan: {s['submitted_at']}\n"
                f"⭐ Sifat: {s['quality_score'] or '—'} | Vaqt: {s['time_score'] or '—'} | Jami: {s['final_score'] or '—'}")
        if s['file_id']:
            if s['file_type'] == 'photo':
                await msg.answer_photo(s['file_id'], caption=text)
            elif s['file_type'] == 'video':
                await msg.answer_video(s['file_id'], caption=text)
            elif s['file_type'] == 'document':
                await msg.answer_document(s['file_id'], caption=text)
        else:
            if s['content']:
                text += f"\n💬 {s['content']}"
            await msg.answer(text)
    await msg.answer("Ko'rish tugadi.", reply_markup=kb.main_menu_inspector())
