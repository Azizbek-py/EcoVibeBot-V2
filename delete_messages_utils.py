"""
Habarlarni avtomatik o'chirishning utility funksiyalari.
"""
import asyncio
import logging
from aiogram import Bot
from aiogram.types import Message

logger = logging.getLogger(__name__)


async def delete_message_after_delay(bot: Bot, message: Message, delay: int = 120):
    """
    Xabarni belgilangan vaqtdan keyin o'chiradi.
    
    Args:
        bot: Telegram bot instance
        message: O'chiriladigan xabar
        delay: O'chirish vaqti (sekund, default: 120)
    """
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id
        )
        logger.info(f"Xabar o'chirildi: {message.message_id} (chat: {message.chat.id})")
    except Exception as e:
        logger.warning(f"Xabar o'chirilmadi: {message.message_id} - {str(e)}")
