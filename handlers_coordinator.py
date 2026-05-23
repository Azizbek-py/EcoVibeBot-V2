from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
import keyboards as kb
from states import CoordMissionStates, AdjustScoreStates

router = Router()


async def is_coordinator(telegram_id: int) -> bool:
    return bool(await db.get_coordinator(telegram_id))


# Missialar start — handlers_common.py da


@router.message(CoordMissionStates.mission_number)
async def coord_missions_show(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_coordinator())
    try:
        mnum = int(msg.text)
    except ValueError:
        return await msg.answer("Son kiriting!")
    await state.clear()
    uid = msg.from_user.id
    groups = await db.get_coordinator_groups(uid)
    if not groups:
        return await msg.answer("Sizga guruh tayinlanmagan.", reply_markup=kb.main_menu_coordinator())

    for gnum in groups:
        subs = await db.get_submissions_for_mission(mnum, gnum)
        for s in subs:
            scored_text = ""
            if s['final_score'] is not None:
                scored_text = f"\n✅ Baholangan: Sifat {s['quality_score']} | Vaqt {s['time_score']} | Jami {s['final_score']}"
            text = (f"👤 {s['full_name']} (Guruh #{s['group_id']})\n"
                    f"📌 Missiya #{s['mission_number']}\n"
                    f"📅 {s['submitted_at']}{scored_text}")
            if s['final_score'] is None:
                ikb = kb.inline_quality_score(s['id'])
            else:
                ikb = None
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
    await msg.answer("Missiya ko'rish tugadi.", reply_markup=kb.main_menu_coordinator())

# Users — handlers_common.py da

# Reyting — handlers_common.py da