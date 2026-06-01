from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
import keyboards as kb
from states import CoordMissionStates, AdjustScoreStates, MissionVerifyStates

router = Router()


async def is_coordinator(telegram_id: int) -> bool:
    return bool(await db.get_coordinator(telegram_id))


# Coordinator-specific cancel handler to ensure cancel returns to coordinator main menu
@router.message(F.text == "❌ Bekor qilish")
async def coord_cancel(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    if not await db.get_coordinator(uid):
        return
    await state.clear()
    await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_coordinator())


# Missialar start — handlers_common.py da


# Users — handlers_common.py da

# Reyting — handlers_common.py da

# Mission verification callback — shows submissions for a specific mission
@router.callback_query(F.data.startswith("verify_mission:"))
async def verify_mission_cb(cb: CallbackQuery, state: FSMContext):
    parts = cb.data.split(":")
    mission_number = int(parts[1])
    mission_type = parts[2] if len(parts) > 2 else "main"
    
    uid = cb.from_user.id
    groups = await db.get_coordinator_groups(uid)
    if not groups:
        await cb.answer("Sizga guruh tayinlanmagan.", show_alert=True)
        return
    
    mission = await db.get_mission(mission_number)
    if not mission:
        await cb.answer("Missiya topilmadi", show_alert=True)
        return
    
    subs = []
    if mission_type == 'archive':
        # Get scored submissions for this mission from coordinator's groups
        for gnum in groups:
            group_subs = await db.get_scored_submissions(mission_number=mission_number, group_number=gnum)
            subs.extend([s for s in group_subs if s['final_score'] is not None])
    else:
        # Get unscored submissions for this mission
        for gnum in groups:
            group_subs = await db.get_submissions_for_mission(mission_number, gnum)
            subs.extend([s for s in group_subs if s['final_score'] is None])
    
    if not subs:
        if mission_type == 'archive':
            await cb.answer("Bu missiya uchun baholangan topshiriq yo'q", show_alert=True)
        else:
            await cb.answer("Bu missiya uchun baholanmagan topshiriq yo'q", show_alert=True)
        return
    
    # Send the mission details
    mission_dict = dict(mission)
    mission_info = (f"📌 Missiya #{mission_number}: {mission_dict['title']}\n"
                   f"{mission_dict['description']}\n"
                   f"🌿 EcoPoint: {mission_dict.get('ecopoint_reward', 0)}\n\n"
                   f"🧾 Jami {len(subs)} ta baholanmagan topshiriq:")
    
    await cb.message.answer(mission_info)
    
    # Show all submissions
    for s in subs:
        scored_text = ""
        if s['final_score'] is not None:
            scored_text = f"\n✅ Baholangan: Sifat {s['quality_score']} | Vaqt {s['time_score']} | Jami {s['final_score']}"
        vip_badge = "👑 " if s['is_vip'] else ""
        text = (f"👤 {vip_badge}{s['full_name']} (Guruh #{s['group_id']})\n"
                f"📌 Missiya #{s['mission_number']}\n"
                f"📅 {s['submitted_at']}{scored_text}")
        if s['final_score'] is None:
            ikb = kb.inline_quality_score(s['id'])
        else:
            ikb = None
        if s['file_id']:
            try:
                if s['file_type'] == 'photo':
                    await cb.message.answer_photo(s['file_id'], caption=text, reply_markup=ikb)
                elif s['file_type'] == 'video':
                    await cb.message.answer_video(s['file_id'], caption=text, reply_markup=ikb)
                elif s['file_type'] == 'document':
                    await cb.message.answer_document(s['file_id'], caption=text, reply_markup=ikb)
                else:
                    # Unknown file type, fallback to text
                    if s['content']:
                        text += f"\n💬 {s['content']}"
                    await cb.message.answer(text, reply_markup=ikb)
            except TelegramBadRequest as exc:
                note = "\n[Media eskirgan va file_id olib tashlandi. Iltimos, missiyani qayta yuboring.]"
                await db.clear_submission_file(s['id'], note)
                try:
                    await cb.message.bot.send_message(
                        s['user_telegram_id'],
                        f"Salom! Missiya #{s['mission_number']} uchun yuborilgan media eskirgan. Iltimos, missiyani qayta yuboring."
                    )
                except Exception:
                    pass
                if s['content']:
                    text += f"\n💬 {s['content']}"
                text += "\n\n[Media yuklab bo'lmadi, foydalanuvchiga qayta yuborish so'raldi]"
                await cb.message.answer(text, reply_markup=ikb)
            except Exception:
                # If sending media fails (network error, etc.), fallback to text to avoid crashing
                if s['content']:
                    text += f"\n💬 {s['content']}"
                text += "\n\n[Media yuklab bo'lmadi]"
                await cb.message.answer(text, reply_markup=ikb)
        else:
            if s['content']:
                text += f"\n💬 {s['content']}"
            await cb.message.answer(text, reply_markup=ikb)
    
    await cb.message.answer("Tekshirish tugadi.", reply_markup=kb.main_menu_coordinator())
    await cb.answer()
