from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


# ══════════════════════════════════════════════
# ADMIN MENYULAR
# ══════════════════════════════════════════════

def main_menu_admin():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📋 Missialar")
    kb.button(text="🔁 Qayta yuborish")
    kb.button(text="👥 Users")
    kb.button(text="🏆 Reyting")
    kb.button(text="🏅 Davriy Reyting")
    kb.button(text="📊 Statistika")
    kb.button(text="🔐 Vakolatlar")
    kb.button(text="📢 Hammaga habar")
    kb.button(text="🛒 Do'kon")
    kb.button(text="🌿 EcoPoint Bo'limi")
    kb.button(text="🏕 Tadbirlar")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def missions_menu_admin():
    """Missiyalar bo'limi: qo'shish, tekshirish, o'chirish, arxiv, deadline"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="➕ Joylash")
    kb.button(text="✅ Tekshirish")
    kb.button(text="🔁 Qayta yuborish")
    kb.button(text="📁 Arxiv Missiyalar")
    kb.button(text="⏰ Deadline belgilash")
    kb.button(text="🗑 Missiyani o'chirish")
    kb.button(text="🔙 Orqaga")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def users_menu_admin():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📋 Ro'yxat")
    kb.button(text="🔍 Qidirish")
    kb.button(text="👥 Guruhlar")
    kb.button(text="🔙 Orqaga")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def vakolatlar_menu_admin():
    """Yangi: Vakolatlar bo'limi — Coordinatorlar, Inspektorlar, Guruhga tayinlash"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="🤝 Coordinatorlar")
    kb.button(text="🔍 Inspektorlar")
    kb.button(text="👥 Guruhga tayinlash")
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

def ecopoint_admin_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🌿 EcoPoint Statistika")
    kb.button(text="🌿 EcoPoint Berish")
    kb.button(text="📜 EcoPoint Tarixi")
    kb.button(text="🔙 Orqaga")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


# ══════════════════════════════════════════════
# COORDINATOR MENYULAR
# ══════════════════════════════════════════════

def main_menu_coordinator():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📋 Missialar")
    kb.button(text="👥 Users")
    kb.button(text="🏆 Reyting")
    kb.button(text="🏅 Davriy Reyting")
    kb.button(text="📊 Statistika")
    kb.button(text="💬 Izohlarni ko'rish")
    kb.button(text="🛒 Do'kon")
    kb.button(text="🏕 Tadbirlar")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


def coord_users_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📋 Ro'yxat")
    kb.button(text="🔍 Qidirish")
    kb.button(text="🔙 Orqaga")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


def missions_menu_coordinator():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📌 Asosiy Missiyalar")
    kb.button(text="⭐ Bonus Missiyalar")
    kb.button(text="📁 Arxiv Missiyalar")
    kb.button(text="🔙 Orqaga")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


# ══════════════════════════════════════════════
# INSPEKTOR MENYULAR
# ══════════════════════════════════════════════

def main_menu_inspector():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📋 Inspektor Missiyalar")
    kb.button(text="👥 Inspektor Users")
    kb.button(text="🏕 Inspektor Tadbirlar")
    kb.button(text="💾 Saqlanganlar")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


# ══════════════════════════════════════════════
# USER MENYULAR
# ══════════════════════════════════════════════

def main_menu_user():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📋 Missialar")
    kb.button(text="👤 Profilim")
    kb.button(text="🏆 Reyting")
    kb.button(text="🏅 Davriy Reyting")
    kb.button(text="🛒 Do'kon")
    kb.button(text="🏕 Tadbirlar")
    kb.button(text="💬 Izoh qoldirish")
    kb.button(text="ℹ️ Bot Haqida")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def shop_menu_user():
    """Do'kon ichki menyusi: xarid qilish + EcoPoint + xaridlarim"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="🛍 Mahsulotlar")
    kb.button(text="🌿 EcoPoint")
    kb.button(text="🧾 Xaridlarim")
    kb.button(text="🔙 Orqaga")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def missions_menu_user():
    """Missiyalar bo'limi tanlash menyusi (user)"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="📌 Asosiy Missiyalar")
    kb.button(text="⭐ Bonus Missiyalar")
    kb.button(text="📜 Tarix")
    kb.button(text="🔙 Orqaga")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


# ══════════════════════════════════════════════
# UMUMIY TUGMALAR
# ══════════════════════════════════════════════

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

def remove_kb():
    return ReplyKeyboardRemove()

def edit_profile_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="✏️ Ism-familiyani o'zgartirish")
    kb.button(text="🏠 Manzilni o'zgartirish")
    kb.button(text="🔙 Orqaga")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


# ══════════════════════════════════════════════
# INLINE TUGMALAR
# ══════════════════════════════════════════════

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
    builder.button(text="➕ EcoPoint qo'shish", callback_data=f"add_eco:{user_telegram_id}:{context}")
    builder.button(text="➖ EcoPoint ayirish", callback_data=f"sub_eco:{user_telegram_id}:{context}")
    builder.adjust(2)
    return builder.as_markup()

def inline_ecopoint_buttons(user_telegram_id: int, context: str = "admin"):
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ EcoPoint qo'shish", callback_data=f"add_eco:{user_telegram_id}:{context}")
    builder.button(text="➖ EcoPoint ayirish", callback_data=f"sub_eco:{user_telegram_id}:{context}")
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

def inline_verify_mission(mission_number: int, mission_type: str = "main"):
    builder = InlineKeyboardBuilder()
    button_text = "🔍 Ko'rish" if mission_type == "archive" else "✅ Tekshirish"
    builder.button(text=button_text, callback_data=f"verify_mission:{mission_number}:{mission_type}")
    return builder.as_markup()


# ══════════════════════════════════════════════
# INSPECTOR INLINE BUTTONS
# ══════════════════════════════════════════════

def missions_category_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📌 Asosiy Missiyalar", callback_data="insp_mission_cat:main")
    builder.button(text="⭐ Bonus Missiyalar", callback_data="insp_mission_cat:bonus")
    builder.adjust(1)
    return builder.as_markup()

def users_submenu_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Ro'yxat", callback_data="insp_users_list")
    builder.button(text="🔍 Qidirish", callback_data="insp_users_search")
    builder.button(text="👥 Guruhlar", callback_data="insp_users_groups")
    builder.adjust(1)
    return builder.as_markup()

def mission_check_button(mission_number: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tekshirish", callback_data=f"insp_mission_check:{mission_number}")
    return builder.as_markup()

def event_check_button(event_number: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tekshirish", callback_data=f"insp_event_check:{event_number}")
    return builder.as_markup()

def info_button(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="ℹ️ Ma'lumot", callback_data=f"insp_user_info:{user_id}")
    return builder.as_markup()


def inline_export_group_button(group_number: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="📤 Guruhni export qilish (JSON)", callback_data=f"export_group:{group_number}")
    return builder.as_markup()

def save_message_button(message_type: str, context_id: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="💾 Saqlash", callback_data=f"insp_save:{message_type}:{context_id}")
    return builder.as_markup()

def delete_saved_item_button(item_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 O'chirish", callback_data=f"insp_delete:{item_id}")
    return builder.as_markup()