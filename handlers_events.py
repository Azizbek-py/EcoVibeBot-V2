from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

import database as db
import keyboards as kb
from states import EventSubmitStates, AddEventStates, EventCheckStates

router = Router()

async def _get_role(uid: int) -> str:
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

async def _send_event_card(msg: Message, event: dict, role: str, user_id: int | None = None):
    text = (
        f"🏕 <b>{event['title']}</b>\n"
        f"🔢 #{event['event_number']}\n"
        f"{event.get('description') or ''}\n\n"
        f"📅 {event.get('event_time') or 'Vaqti belgilanmagan'}\n"
        f"🏆 Ball: {event.get('ball_reward', 0)} | 🌿 Eco: {event.get('eco_reward', 0)}\n"
        f"🌍 Hudud: {event.get('region') or 'Barchasi'}"
    )

    reply_markup = None
    if role == "user" and user_id is not None:
        submitted = await db.get_event_submission(user_id, event['event_number'])
        if not submitted:
            builder = InlineKeyboardBuilder()
            builder.button(text="📤 Tadbir topshirish", callback_data=f"submit_event:{event['event_number']}")
            builder.adjust(1)
            reply_markup = builder.as_markup()

    if event.get('photo_file_id'):
        await msg.answer_photo(event['photo_file_id'], caption=text, parse_mode="HTML", reply_markup=reply_markup)
    else:
        await msg.answer(text, parse_mode="HTML", reply_markup=reply_markup)


@router.message(F.text == "🏕 Tadbirlar")
async def show_events(msg: Message, state: FSMContext, bot: Bot):
    uid = msg.from_user.id
    role = await _get_role(uid)
    if role == "none":
        return

    if role == "user":
        from subscription import subscription_guard
        if not await subscription_guard(msg, bot):
            return
        user = await db.get_user(uid)
        events = await db.get_events(user['region'] if user else None)
    else:
        events = await db.get_events()

    if role == "admin":
        kb_builder = ReplyKeyboardBuilder()
        kb_builder.button(text="➕ Tadbir qo'shish")
        kb_builder.button(text="🗑 Tadbirni o'chirish")
        kb_builder.button(text="🔙 Orqaga")
        kb_builder.adjust(2)
        await msg.answer("Tadbirlar bo'limi:", reply_markup=kb_builder.as_markup(resize_keyboard=True))

    if not events:
        text = "Hozircha tadbirlar yo'q."
        if role == "admin":
            return
        if role == "coordinator":
            return await msg.answer(text, reply_markup=kb.main_menu_coordinator())
        if role == "user":
            return await msg.answer(text, reply_markup=kb.main_menu_user())
        return

    if role == "admin":
        await msg.answer("Joriy tadbirlar:")
    elif role == "coordinator":
        await msg.answer("Joriy tadbirlar:")
    else:
        await msg.answer("Tadbirlar ro'yxati:")

    for event in events:
        await _send_event_card(msg, event, role, uid if role == "user" else None)


@router.callback_query(F.data.startswith("submit_event:"))
async def submit_event_start(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    user = await db.get_user(uid)
    if not user:
        return await cb.answer("Avval ro'yxatdan o'ting!", show_alert=True)

    try:
        event_number = int(cb.data.split(":")[1])
    except (IndexError, ValueError):
        return await cb.answer("Noto'g'ri tadbir raqami.", show_alert=True)

    event = await db.get_event(event_number)
    if not event or event.get('is_active') != 1:
        return await cb.answer("Tadbir topilmadi yoki faol emas.", show_alert=True)

    await state.update_data(event_number=event_number)
    await cb.message.answer("📸 Tadbir uchun fotosurat yuboring:", reply_markup=kb.cancel_kb())
    await state.set_state(EventSubmitStates.photo)
    await cb.answer()


@router.message(EventSubmitStates.photo)
async def submit_event_photo(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    data = await state.get_data()
    event_number = data.get('event_number')
    if not event_number:
        await state.clear()
        return await msg.answer("Ishni qayta boshlang.", reply_markup=kb.main_menu_user())

    if not msg.photo:
        return await msg.answer("Iltimos tadbir uchun fotosurat yuboring.", reply_markup=kb.cancel_kb())

    photo_file_id = msg.photo[-1].file_id
    await db.submit_event(uid, event_number, photo_file_id)
    await state.clear()
    await msg.answer("✅ Fotosurat qabul qilindi. Inspektor tekshiradi.", reply_markup=kb.main_menu_user())


@router.message(F.text == "➕ Tadbir qo'shish")
async def add_event_start(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    if await _get_role(uid) != "admin":
        return
    await msg.answer("Tadbir raqamini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(AddEventStates.number)


@router.message(AddEventStates.number)
async def add_event_number(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_admin())
    try:
        number = int(msg.text)
    except ValueError:
        return await msg.answer("Iltimos, son kiriting!")
    await state.update_data(number=number)
    await msg.answer("Tadbir sarlavhasini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(AddEventStates.title)


@router.message(AddEventStates.title)
async def add_event_title(msg: Message, state: FSMContext):
    await state.update_data(title=msg.text)
    await msg.answer("Tadbir tavsifini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(AddEventStates.description)


@router.message(AddEventStates.description)
async def add_event_description(msg: Message, state: FSMContext):
    await state.update_data(description=msg.text)
    await msg.answer("Tadbir vaqtini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(AddEventStates.event_time)


@router.message(AddEventStates.event_time)
async def add_event_time(msg: Message, state: FSMContext):
    await state.update_data(event_time=msg.text)
    await msg.answer("Tadbir uchun ball miqdorini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(AddEventStates.ball_reward)


@router.message(AddEventStates.ball_reward)
async def add_event_ball(msg: Message, state: FSMContext):
    try:
        ball_reward = float(msg.text)
    except ValueError:
        return await msg.answer("Iltimos, son kiriting!")
    await state.update_data(ball_reward=ball_reward)
    await msg.answer("Tadbir uchun EcoPoint miqdorini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(AddEventStates.eco_reward)


@router.message(AddEventStates.eco_reward)
async def add_event_eco(msg: Message, state: FSMContext):
    try:
        eco_reward = float(msg.text)
    except ValueError:
        return await msg.answer("Iltimos, son kiriting!")
    await state.update_data(eco_reward=eco_reward)
    await msg.answer("Hududni kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(AddEventStates.region)


@router.message(AddEventStates.region)
async def add_event_region(msg: Message, state: FSMContext):
    await state.update_data(region=msg.text)
    await msg.answer("Tadbir uchun fotosurat yuboring:", reply_markup=kb.cancel_kb())
    await state.set_state(AddEventStates.photo)


@router.message(AddEventStates.photo)
async def add_event_photo(msg: Message, state: FSMContext):
    if not msg.photo:
        return await msg.answer("Iltimos, rasm yuboring.", reply_markup=kb.cancel_kb())

    data = await state.get_data()
    await db.add_event(
        data['number'],
        data['title'],
        data['description'],
        data['event_time'],
        data['ball_reward'],
        data['eco_reward'],
        data['region'],
        msg.photo[-1].file_id
    )
    await state.clear()
    await msg.answer("✅ Tadbir saqlandi.", reply_markup=kb.main_menu_admin())


@router.message(F.text == "🗑 Tadbirni o'chirish")
async def delete_event_start(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    if await _get_role(uid) != "admin":
        return
    await msg.answer("O'chirish uchun tadbir raqamini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(EventCheckStates.event_number)


@router.message(EventCheckStates.event_number)
async def delete_event_confirm(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        return await msg.answer("Bekor qilindi.", reply_markup=kb.main_menu_admin())
    try:
        event_number = int(msg.text)
    except ValueError:
        return await msg.answer("Iltimos, son kiriting!")

    event = await db.get_event(event_number)
    if not event:
        return await msg.answer("Bunday tadbir topilmadi.")

    await db.delete_event(event_number)
    await state.clear()
    await msg.answer("✅ Tadbir o'chirildi.", reply_markup=kb.main_menu_admin())
