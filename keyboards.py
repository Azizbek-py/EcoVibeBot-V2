from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_menu_admin():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📋 Missialar")
    kb.button(text="👥 Users")
    kb.button(text="🏆 Reyting")
    kb.button(text="🏅 Davriy Reyting")
    kb.button(text="📊 Statistika")
    kb.button(text="🔍 Inspektorlar")
    kb.button(text="🤝 Coordinators")
    kb.button(text="👥 Guruhga tayinlash")
    kb.button(text="📢 Hammaga habar")
    kb.button(text="📁 Arxiv Missialar")
    kb.button(text="⏰ Deadline belgilash")
    kb.button(text="💬 Izohlarni ko'rish")
    kb.button(text="🛒 Do'kon")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def missions_menu_admin():
    kb = ReplyKeyboardBuilder()
    kb.button(text="➕ Joylash")
    kb.button(text="✅ Tekshirish")
    kb.button(text="🗑 Missiyani o'chirish")
    kb.button(text="🔙 Orqaga")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def users_menu_admin():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📋 Ro'yxat")
    kb.button(text="🔍 Qidirish")
    kb.button(text="👥 Guruhdan qidirish")
    kb.button(text="🔙 Orqaga")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def coordinators_menu_admin():
    kb = ReplyKeyboardBuilder()
    kb.button(text="➕ Coordinator Tayinlash")
    kb.button(text="📋 Coordinator Ro'yxat")
    kb.button(text="🔙 Orqaga")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def inspectors_menu_admin():
    kb = ReplyKeyboardBuilder()
    kb.button(text="➕ Inspektor Tayinlash")
    kb.button(text="📋 Inspektor Ro'yxat")
    kb.button(text="🔙 Orqaga")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def back_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🔙 Orqaga")
    return kb.as_markup(resize_keyboard=True)

def cancel_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="❌ Bekor qilish")
    return kb.as_markup(resize_keyboard=True)

def phone_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📱 Telefon raqamni yuborish", request_contact=True)
    kb.button(text="❌ Bekor qilish")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)

def main_menu_coordinator():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📋 Missialar")
    kb.button(text="👥 Users")
    kb.button(text="🏆 Reyting")
    kb.button(text="🏅 Davriy Reyting")
    kb.button(text="📊 Statistika")
    kb.button(text="📁 Arxiv Missialar")
    kb.button(text="💬 Izohlarni ko'rish")
    kb.button(text="🛒 Do'kon")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def main_menu_inspector():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📋 Missialar")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)

def main_menu_user():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📋 Missialar")
    kb.button(text="👤 Profilim")
    kb.button(text="🏆 Reyting")
    kb.button(text="🏅 Davriy Reyting")
    kb.button(text="🛒 Do'kon")
    kb.button(text="🧾 Xaridlarim")
    kb.button(text="💬 Izoh qoldirish")
    kb.button(text="ℹ️ Bot Haqida")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def remove_kb():
    return ReplyKeyboardRemove()

def inline_score_buttons(submission_id: int):
    builder = InlineKeyboardBuilder()
    for score in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
        builder.button(text=str(score), callback_data=f"score:{submission_id}:{score}")
    builder.adjust(5)
    return builder.as_markup()

def inline_delete_mission(mission_number: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 O'chirish", callback_data=f"del_mission:{mission_number}")
    return builder.as_markup()

def inline_delete_coordinator(telegram_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 O'chirish", callback_data=f"del_coord:{telegram_id}")
    return builder.as_markup()

def inline_delete_inspector(telegram_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 O'chirish", callback_data=f"del_insp:{telegram_id}")
    return builder.as_markup()

def inline_user_score_buttons(user_telegram_id: int, context: str = "admin"):
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Ball qo'shish", callback_data=f"add_score:{user_telegram_id}:{context}")
    builder.button(text="➖ Ball ayirish", callback_data=f"sub_score:{user_telegram_id}:{context}")
    builder.adjust(2)
    return builder.as_markup()

def inline_submit_mission(mission_number: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="📤 Missiyani joylash", callback_data=f"submit_mission:{mission_number}")
    return builder.as_markup()

def inline_quality_score(submission_id: int):
    builder = InlineKeyboardBuilder()
    for score in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
        builder.button(text=str(score), callback_data=f"quality:{submission_id}:{score}")
    builder.adjust(5)
    return builder.as_markup()

def inline_time_score(submission_id: int, quality: float):
    builder = InlineKeyboardBuilder()
    for score in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
        builder.button(text=str(score), callback_data=f"time_sc:{submission_id}:{score}:{quality}")
    builder.adjust(5)
    return builder.as_markup()

def inline_archive_score(submission_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Ball qo'shish", callback_data=f"arch_add:{submission_id}")
    builder.button(text="➖ Ball ayirish", callback_data=f"arch_sub:{submission_id}")
    builder.adjust(2)
    return builder.as_markup()

def edit_profile_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="✏️ Ism-familiyani o'zgartirish")
    kb.button(text="🏠 Manzilni o'zgartirish")
    kb.button(text="🔙 Orqaga")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)