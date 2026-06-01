from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, StateFilter

import database as db
from subscription import subscription_guard, check_subscription, subscription_keyboard
from levels import get_level, get_next_level
import keyboards as kb
from states import RegisterStates, SubmitMissionStates, EditProfileStates

UZBEKISTAN_REGIONS = [
    "Toshkent shahri", "Toshkent viloyati", "Andijon", "Farg'ona", "Namangan",
    "Samarqand", "Buxoro", "Navoiy", "Qashqadaryo", "Surxondaryo",
    "Jizzax", "Sirdaryo", "Xorazm", "Qoraqalpog'iston"
]

def regions_kb():
    from aiogram.utils.keyboard import ReplyKeyboardBuilder as RKB
    kb_b = RKB()
    for r in UZBEKISTAN_REGIONS:
        kb_b.button(text=r)
    kb_b.button(text="❌ Bekor qilish")
    kb_b.adjust(3)
    return kb_b.as_markup(resize_keyboard=True)



async def only_regular_user(uid: int) -> bool:
    """Returns True only if user is a regular participant (not admin/coord/inspector)"""
    from handlers_admin import is_admin
    if is_admin(uid):
        return False
    if await db.get_coordinator(uid):
        return False
    if await db.get_inspector(uid):
        return False
    if not await db.get_user(uid):
        return False
    return True



router = Router()

_pending_submission = {}  # user_id -> mission_number


@router.message(CommandStart(deep_link=False))
async def start_cmd(msg: Message, state: FSMContext, bot: Bot):
    uid = msg.from_user.id
    await state.clear()

    # Majburiy kanal obunasini tekshirish
    if not await subscription_guard(msg, bot):
        return

    # Rol tekshiruvi — avval rol, keyin oddiy user
    from handlers_admin import is_admin
    if is_admin(uid):
        return await msg.answer("Admin panelga xush kelibsiz! /admin", reply_markup=kb.main_menu_admin())
    if await db.get_coordinator(uid):
        coord = await db.get_coordinator(uid)
        return await msg.answer(
            f"Coordinator paneliga xush kelibsiz, {coord['full_name']}! 👋",
            reply_markup=kb.main_menu_coordinator()
        )
    if await db.get_inspector(uid):
        insp = await db.get_inspector(uid)
        return await msg.answer(
            f"Inspektor paneliga xush kelibsiz, {insp['full_name']}! 👋",
            reply_markup=kb.main_menu_inspector()
        )

    # Oddiy user
    user = await db.get_user(uid)
    if user:
        return await msg.answer(
            f"Xush kelibsiz, {user['full_name']}! 👋",
            reply_markup=kb.main_menu_user()
        )

    # Ro'yxatdan o'tmagan — ro'yxatdan o'tkazish
    await msg.answer(
        "Xush kelibsiz! Ro'yxatdan o'tish uchun ism-familiyangizni kiriting:",
        reply_markup=kb.cancel_kb()
    )
    await state.set_state(RegisterStates.full_name)


# User-specific cancel handler to ensure cancel returns to user main menu
@router.message(F.text == "❌ Bekor qilish")
async def user_cancel(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    await state.clear()
    await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_user())


@router.callback_query(F.data == "check_sub")
async def check_sub_callback(cb: CallbackQuery, bot: Bot):
    """Foydalanuvchi obuna bo'ldim tugmasini bosganda tekshirish."""
    not_subscribed = await check_subscription(bot, cb.from_user.id)
    if not not_subscribed:
        await cb.message.delete()
        await cb.answer("✅ Rahmat! Endi botdan foydalanishingiz mumkin.", show_alert=True)
        # /start ni qayta ishga tushirish
        uid = cb.from_user.id
        from handlers_admin import is_admin
        if is_admin(uid):
            await cb.message.answer("Admin panelga xush kelibsiz! /admin", reply_markup=kb.main_menu_admin())
        elif await db.get_coordinator(uid):
            coord = await db.get_coordinator(uid)
            await cb.message.answer(f"Coordinator paneliga xush kelibsiz, {coord['full_name']}! 👋", reply_markup=kb.main_menu_coordinator())
        elif await db.get_inspector(uid):
            insp = await db.get_inspector(uid)
            await cb.message.answer(f"Inspektor paneliga xush kelibsiz, {insp['full_name']}! 👋", reply_markup=kb.main_menu_inspector())
        elif await db.get_user(uid):
            user = await db.get_user(uid)
            await cb.message.answer(f"Xush kelibsiz, {user['full_name']}! 👋", reply_markup=kb.main_menu_user())
        else:
            await cb.message.answer("Xush kelibsiz! Ro'yxatdan o'tish uchun ism-familiyangizni kiriting:", reply_markup=kb.cancel_kb())
    else:
        channels_text = "\n".join([f"  • {ch}" for ch in not_subscribed])
        await cb.answer("❌ Siz hali obuna bo'lmagansiz!", show_alert=True)
        await cb.message.edit_reply_markup(reply_markup=subscription_keyboard(not_subscribed))


@router.message(RegisterStates.full_name)
async def reg_full_name(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.")
    await state.update_data(full_name=msg.text)
    await msg.answer("Telefon raqamingizni yuboring:", reply_markup=kb.phone_kb())
    await state.set_state(RegisterStates.phone)


@router.message(RegisterStates.phone)
async def reg_phone(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.")
    phone = None
    if msg.contact:
        phone = msg.contact.phone_number
    elif msg.text:
        phone = msg.text
    if not phone:
        return await msg.answer("Iltimos telefon raqamingizni yuboring.")
    await state.update_data(phone=phone)
    await msg.answer("🗺 Viloyatingizni tanlang:", reply_markup=regions_kb())
    await state.set_state(RegisterStates.address)


@router.message(RegisterStates.address)
async def reg_address(msg: Message, state: FSMContext, bot: Bot):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.")
    if msg.text not in UZBEKISTAN_REGIONS:
        return await msg.answer("Iltimos, ro'yxatdan viloyat tanlang!", reply_markup=regions_kb())
    data = await state.get_data()
    uid = msg.from_user.id
    group_num = await db.register_user(uid, data["full_name"], data["phone"], msg.text)

    # Referral — FAQAT taklif qiluvchiga EcoPoint beriladi
    referrer_id = data.get("referrer_id")
    referral_msg = ""
    if referrer_id:
        from ecopoint import ECOPOINT_REWARDS
        set_ok = await db.set_referral(uid, referrer_id)
        if set_ok:
            # Faqat taklif qiluvchiga beriladi, yangi userga EMAS
            await db.add_ecopoints(referrer_id, ECOPOINT_REWARDS["referral"], f"Do'st taklifi: {data['full_name']}")
            try:
                referrer = await db.get_user(referrer_id)
                if referrer:
                    await bot.send_message(
                        referrer_id,
                        f"🎉 Do'stingiz <b>{data['full_name']}</b> ro'yxatdan o'tdi!\n"
                        f"🌿 +{ECOPOINT_REWARDS['referral']} EcoPoint berildi!",
                        parse_mode="HTML"
                    )
            except Exception:
                pass

    await state.clear()
    await msg.answer(
        f"✅ Ro'yxatdan o'tdingiz!\n"
        f"👥 Siz {group_num}-guruhga kiritildingiz.{referral_msg}",
        reply_markup=kb.main_menu_user()
    )


# ── Missions for user ──────────────────────────────────────────
@router.callback_query(F.data.startswith("submit_mission:"))
async def submit_mission_start(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    user = await db.get_user(uid)
    if not user:
        return await cb.answer("Avval ro'yxatdan o'ting!")
    mnum = int(cb.data.split(":")[1])
    await state.update_data(mission_number=mnum)
    await cb.message.answer(
        f"📤 Missiya mid{mnum} uchun javobingizni yuboring (matn, rasm, video yoki fayl):",
        reply_markup=kb.cancel_kb()
    )
    await state.set_state(SubmitMissionStates.content)
    await cb.answer()


@router.message(SubmitMissionStates.content)
async def submit_mission_content(msg: Message, state: FSMContext, bot: Bot):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_user())
    data = await state.get_data()
    mnum = data["mission_number"]
    uid = msg.from_user.id
    file_id = None
    file_type = None
    content = msg.text or ""
    if msg.photo:
        file_id = msg.photo[-1].file_id
        file_type = "photo"
    elif msg.video:
        file_id = msg.video.file_id
        file_type = "video"
    elif msg.document:
        file_id = msg.document.file_id
        file_type = "document"
    # Validate file_id: if it's an HTTP URL or looks like a non-telegram identifier,
    # don't save it into file_id (Telegram will reject when sending). Move it to content instead.
    if file_id:
        fid = file_id.strip()
        if fid.startswith("http://") or fid.startswith("https://") or "http" in fid:
            # append URL to content and clear file fields
            content = (content + "\n" if content else "") + f"[Link yuborildi] {fid}"
            file_id = None
            file_type = None

    await db.submit_mission(uid, mnum, content, file_id, file_type)
    await state.clear()
    await msg.answer("✅ Missiya topshirildi! Coordinator tekshirishini kuting.", reply_markup=kb.main_menu_user())
    # Notify coordinators
    user = await db.get_user(uid)
    if user:
        coords = await db.get_group_coordinators(user['group_id'])
        for coord in coords:
            try:
                text = (f"📬 Yangi topshiriq!\n"
                        f"👤 {user['full_name']} (Guruh #{user['group_id']})\n"
                        f"📌 Missiya mid{mnum}")
                # Get submission id
                sub = await db.get_submission(uid, mnum)
                if sub:
                    ikb = kb.inline_quality_score(sub['id'])
                    if file_id:
                        if file_type == 'photo':
                            await bot.send_photo(coord['telegram_id'], file_id, caption=text, reply_markup=ikb)
                        elif file_type == 'video':
                            await bot.send_video(coord['telegram_id'], file_id, caption=text, reply_markup=ikb)
                        elif file_type == 'document':
                            await bot.send_document(coord['telegram_id'], file_id, caption=text, reply_markup=ikb)
                    else:
                        if content:
                            text += f"\n💬 {content}"
                        await bot.send_message(coord['telegram_id'], text, reply_markup=ikb)
            except Exception:
                pass


# ── Profile ────────────────────────────────────────────────────
@router.message(F.text == "👤 Profilim")
async def user_profile(msg: Message):
    uid = msg.from_user.id
    user = await db.get_user(uid)
    if not user:
        return
    coords = await db.get_group_coordinators(user['group_id'] or 0)
    coord_info = ", ".join([f"{c['full_name']} (@{c['username'] or c['telegram_id']})" for c in coords]) or "Tayinlanmagan"
    current_level = get_level(user['score'])
    next_name, balls_needed = get_next_level(user['score'])
    next_info = f"\n📈 Keyingi daraja: {next_name} (yana {balls_needed:.1f} ball)" if next_name else "\n🏆 Eng yuqori daraja!"
    vip_line = "\n👑 <b>VIP</b> foydalanuvchi" if user['is_vip'] else ""
    eco_points = user['ecopoints'] if user['ecopoints'] is not None else 0
    text = (f"👤 {user['full_name']}{vip_line}\n"
            f"🆔 {user['telegram_id']}\n"
            f"📱 {user['phone']}\n"
            f"🏠 {user['address']}\n"
            f"👥 Guruh #{user['group_id']}\n"
            f"🤝 Coordinator: {coord_info}\n"
            f"⭐ Ball: {user['score']}\n"
            f"🌿 EcoPoint: {eco_points}\n"
            f"🎖 Daraja: {current_level}{next_info}")
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Profilni tahrirlash", callback_data="edit_profile")
    await msg.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "edit_profile")
async def edit_profile_start(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("Nima o'zgartirmoqchisiz?", reply_markup=kb.edit_profile_kb())
    await state.set_state(EditProfileStates.choose_field)
    await cb.answer()


@router.message(StateFilter(EditProfileStates.choose_field, EditProfileStates.full_name, EditProfileStates.address), F.text == "🔙 Orqaga")
async def edit_profile_back(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Menyu", reply_markup=kb.main_menu_user())


@router.message(EditProfileStates.choose_field)
async def edit_profile_choose(msg: Message, state: FSMContext):
    if msg.text == "✏️ Ism-familiyani o'zgartirish":
        await state.set_state(EditProfileStates.full_name)
        await msg.answer("Yangi ism-familiyangizni kiriting:", reply_markup=kb.back_kb())
    elif msg.text == "🏠 Manzilni o'zgartirish":
        await state.set_state(EditProfileStates.address)
        await msg.answer("Yangi manzilingizni kiriting:", reply_markup=kb.back_kb())
    elif msg.text == "🔙 Orqaga":
        await state.clear()
        await msg.answer("Menyu", reply_markup=kb.main_menu_user())


@router.message(EditProfileStates.full_name)
async def edit_full_name(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_user())
    await db.update_user_profile(msg.from_user.id, full_name=msg.text)
    await state.clear()
    await msg.answer("✅ Ism-familiya yangilandi!", reply_markup=kb.main_menu_user())


@router.message(EditProfileStates.address)
async def edit_address(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_user())
    await db.update_user_profile(msg.from_user.id, address=msg.text)
    await state.clear()
    await msg.answer("✅ Manzil yangilandi!", reply_markup=kb.main_menu_user())


# ── Rating for user ────────────────────────────────────────────
@router.message(F.text == "ℹ️ Bot Haqida")
async def bot_about(msg: Message):
    uid = msg.from_user.id
    if not await only_regular_user(uid):
        return
    await msg.answer(
       "<b>🚀 LevelUP Challenge Bot’ga xush kelibsiz! \n\n</b>"

        "Ushbu bot zamonaviy online challenge va missiyalar tizimi uchun @MrSaxiy tomonidan maxsus ishlab chiqilgan. Bot orqali foydalanuvchilar turli challenge va topshiriqlarda qatnashishi mumkin. \n\n"
        "<b>⚡️ Bot imkoniyatlari:\n</b>"
        "• Challenge va missiyalarda qatnashish\n"
        "• Foto, video, fayl va matn yuborish\n"
        "• Ball va reyting tizimi\n"
        "• Avtomatik tekshiruv va boshqaruv\n"
        "• To'plangan ballarni almashtirish\n"
        "• Qulay va tezkor interfeys\n\n"
        "<b>Darajalar va ballar:\n</b>"
        "   Askar 🪖 (0 ball -> 50)\n"
        "   Serjant ⚔️ (50 ball -> 100)\n"
        "   Leytenant 🎯 (100 ball -> 150)\n"
        "   Kapitan 🛡 (150 ball -> 200)\n"
        "   Mayor 🔥 (200 ball -> 250)\n"
        "   Polkovnik 🎖 (250 ball -> 300)\n"
        "   Imperator 👑 (300 ball -> ...)\n\n"

        "🔥 O‘zingizni sinab ko‘ring, missiyalarni bajaring va eng faol ishtirokchilar safiga qo'shiling! \n "
        "👨‍💻Admin: @MrSaxiy",
        parse_mode="HTML"
    )

