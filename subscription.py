"""
Majburiy kanal obunasini tekshirish moduli.
Kanallar .env faylda REQUIRED_CHANNELS=@kanal1,@kanal2,@kanal3 ko'rinishida sozlanadi.
"""
import os
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_required_channels() -> list:
    """REQUIRED_CHANNELS env o'zgaruvchisidan kanallar ro'yxatini olish."""
    channels = os.getenv("REQUIRED_CHANNELS", "")
    return [ch.strip() for ch in channels.split(",") if ch.strip()]


async def check_subscription(bot: Bot, user_id: int) -> list:
    """
    Foydalanuvchi obuna bo'lmagan kanallar ro'yxatini qaytaradi.
    Bo'sh ro'yxat = hammaga obuna.
    """
    channels = get_required_channels()
    not_subscribed = []
    for channel in channels:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status in ("left", "kicked", "banned"):
                not_subscribed.append(channel)
        except Exception:
            # Kanal topilmasa yoki bot admin bo'lmasa — o'tkazib yuborish
            pass
    return not_subscribed


def subscription_keyboard(not_subscribed: list) -> InlineKeyboardMarkup:
    """Obuna bo'lmagan kanallar uchun tugmalar."""
    builder = InlineKeyboardBuilder()
    for channel in not_subscribed:
        # @ belgisini olib tashlash
        clean = channel.lstrip("@")
        builder.button(text=f"📢 {channel} ga obuna bo'lish", url=f"https://t.me/{clean}")
    builder.button(text="✅ Obuna bo'ldim, tekshirish", callback_data="check_sub")
    builder.adjust(1)
    return builder.as_markup()


async def subscription_guard(message: Message, bot: Bot) -> bool:
    """
    True qaytarsa — obuna qilingan, davom etish mumkin.
    False qaytarsa — xabar yuborildi, to'xtatish kerak.
    """
    not_subscribed = await check_subscription(bot, message.from_user.id)
    if not not_subscribed:
        return True

    channels_text = "\n".join([f"  • {ch}" for ch in not_subscribed])
    await message.answer(
        f"⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'lishingiz kerak:\n\n"
        f"{channels_text}\n\n"
        f"Obuna bo'lgach, <b>✅ Obuna bo'ldim</b> tugmasini bosing.",
        parse_mode="HTML",
        reply_markup=subscription_keyboard(not_subscribed)
    )
    return False
