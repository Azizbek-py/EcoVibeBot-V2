import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import database as db
import handlers_admin as admin_h
import handlers_coordinator as coord_h
import handlers_inspector as insp_h
import handlers_user as user_h
import handlers_common as common_h
import handlers_extra as extra_h
import handlers_shop as shop_h
import handlers_ecopoint as eco_h
import handlers_events as events_h

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN .env faylida ko'rsatilmagan!")

    admin_ids = []
    for aid in ADMIN_ID.split(","):
        aid = aid.strip()
        if aid.isdigit():
            admin_ids.append(int(aid))
    admin_h.set_admin_ids(admin_ids)

    await db.init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(common_h.router)
    dp.include_router(events_h.router)
    dp.include_router(eco_h.router)
    dp.include_router(shop_h.router)
    dp.include_router(extra_h.router)
    dp.include_router(user_h.router)
    dp.include_router(admin_h.router)
    dp.include_router(coord_h.router)
    dp.include_router(insp_h.router)

    logger.info("Bot ishga tushmoqda...")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())




