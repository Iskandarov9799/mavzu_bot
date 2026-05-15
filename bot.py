import asyncio
import logging
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Awaitable, Any, Dict
from config import config

class PrivateChatMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            if event.web_app_data:
                return await handler(event, data)
            if event.chat.type != "private":
                return
            from database.db import is_banned
            if await is_banned(event.from_user.id):
                await event.answer("🚫 Siz botdan bloklangansiz.")
                return
        elif isinstance(event, CallbackQuery):
            if event.message and event.message.chat.type != "private":
                return
            from database.db import is_banned
            if await is_banned(event.from_user.id):
                await event.answer("🚫 Bloklangansiz.", show_alert=True)
                return
        return await handler(event, data)

logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    config.validate()
    from database.connection import init_engine, init_db
    init_engine()
    await init_db()

    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp  = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(PrivateChatMiddleware())
    dp.callback_query.middleware(PrivateChatMiddleware())

    from handlers import registration, test_handler, payment, admin, miniapp_handler
    dp.include_router(admin.router)
    dp.include_router(miniapp_handler.router)
    dp.include_router(registration.router)
    dp.include_router(payment.router)
    dp.include_router(test_handler.router)

    logger.info("🚀 Bot ishga tushdi! Admin IDs: %s", config.ADMIN_IDS)
    try:
        await dp.start_polling(bot, allowed_updates=["message","callback_query","web_app_data"])
    except KeyboardInterrupt:
        pass
    finally:
        await bot.session.close()
        logger.info("🛑 Bot to'xtatildi.")

if __name__ == "__main__":
    asyncio.run(main())
