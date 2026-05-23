from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

import database as db
from levels import get_level, get_next_level
import keyboards as kb
from states import RegisterStates, SubmitMissionStates, EditProfileStates

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


@router.message(Command("start"))
async def start_cmd(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    await state.clear()

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
    await msg.answer("Yashash manzilingizni kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(RegisterStates.address)


@router.message(RegisterStates.address)
async def reg_address(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.")
    data = await state.get_data()
    group_num = await db.register_user(msg.from_user.id, data["full_name"], data["phone"], msg.text)
    await state.clear()
    await msg.answer(
        f"✅ Ro'yxatdan o'tdingiz!\n"
        f"👥 Siz {group_num}-guruhga kiritildingiz.",
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
        f"📤 Missiya #{mnum} uchun javobingizni yuboring (matn, rasm, video yoki fayl):",
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
                        f"📌 Missiya #{mnum}")
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
    text = (f"👤 {user['full_name']}{vip_line}\n"
            f"🆔 {user['telegram_id']}\n"
            f"📱 {user['phone']}\n"
            f"🏠 {user['address']}\n"
            f"👥 Guruh #{user['group_id']}\n"
            f"🤝 Coordinator: {coord_info}\n"
            f"⭐ Ball: {user['score']}\n"
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


@router.message(EditProfileStates.choose_field)
async def edit_profile_choose(msg: Message, state: FSMContext):
    if msg.text == "✏️ Ism-familiyani o'zgartirish":
        await state.set_state(EditProfileStates.full_name)
        await msg.answer("Yangi ism-familiyangizni kiriting:", reply_markup=kb.cancel_kb())
    elif msg.text == "🏠 Manzilni o'zgartirish":
        await state.set_state(EditProfileStates.address)
        await msg.answer("Yangi manzilingizni kiriting:", reply_markup=kb.cancel_kb())
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
        "🚀 LevelUP Challenge Bot’ga xush kelibsiz!\n\n"
        "Ushbu bot zamonaviy online challenge va missiyalar tizimi uchun maxsus ishlab chiqilgan. Bot orqali foydalanuvchilar turli challenge va topshiriqlarda qatnashishi, missiyalarni bajarishi, natijalarni yuborishi hamda reyting va ballar yig‘ishi mumkin.\n\n"
        "⚡️ Bot imkoniyatlari:\n"
        "• Challenge va missiyalarda qatnashish\n"
        "• Foto, video, fayl va matn yuborish\n"
        "• Ball va reyting tizimi\n"
        "• Avtomatik tekshiruv va boshqaruv\n"
        "• To'plangan ballarni almashtirish\n"
        "• Qulay va tezkor interfeys\n\n"
        "🎯 Bizning maqsad:\n"
        "Yoshlarni faol, kreativ va intizomli bo‘lishga undash hamda online challenge’larni yanada qiziqarli va professional darajaga olib chiqish.\n\n"
        "🔥 O‘zingizni sinab ko‘ring, missiyalarni bajaring va eng faol ishtirokchilar safiga qo'shiling! \n"
        "Admin: @MrSaxiy"
    )


