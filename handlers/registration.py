import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from database.db import create_user, update_user_phone, is_registered, get_user
from keyboards.keyboards import phone_keyboard, main_menu_keyboard, admin_keyboard
from states import RegistrationStates
from config import config

router = Router()
logger = logging.getLogger(__name__)

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    tid  = message.from_user.id
    name = message.from_user.full_name or "Foydalanuvchi"

    await create_user(tid, name, message.from_user.username)

    if await is_registered(tid):
        if tid in config.ADMIN_IDS:
            await message.answer(
                f"👋 Xush kelibsiz, <b>{name}</b>!\n\nAdmin panel:",
                reply_markup=admin_keyboard(), parse_mode="HTML"
            )
        else:
            await message.answer(
                f"👋 Xush kelibsiz, <b>{name}</b>!\n\nFan tanlang:",
                reply_markup=main_menu_keyboard(), parse_mode="HTML"
            )
        return

    await message.answer(
        f"👋 Salom, <b>{name}</b>!\n\n"
        f"📚 <b>Ona tili va Adabiyot Test Botiga xush kelibsiz!</b>\n\n"
        f"Davom etish uchun telefon raqamingizni ulashing 👇",
        reply_markup=phone_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(RegistrationStates.waiting_phone)

@router.message(RegistrationStates.waiting_phone, F.contact)
async def receive_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    if not phone.startswith("+"): phone = "+" + phone
    await update_user_phone(message.from_user.id, phone)
    await state.clear()

    tid = message.from_user.id
    if tid in config.ADMIN_IDS:
        await message.answer(
            "✅ <b>Ro'yxatdan o'tdingiz!</b>",
            reply_markup=admin_keyboard(), parse_mode="HTML"
        )
    else:
        await message.answer(
            "✅ <b>Ro'yxatdan o'tdingiz!</b>\n\nFan tanlang:",
            reply_markup=main_menu_keyboard(), parse_mode="HTML"
        )

@router.message(RegistrationStates.waiting_phone)
async def phone_not_shared(message: Message):
    await message.answer(
        "📱 Iltimos, <b>tugmani bosib</b> telefon raqamingizni ulashing:",
        reply_markup=phone_keyboard(), parse_mode="HTML"
    )

@router.message(F.text == "🔙 Orqaga")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    if message.from_user.id in config.ADMIN_IDS:
        await message.answer("Admin panel:", reply_markup=admin_keyboard())
    else:
        await message.answer("Fan tanlang:", reply_markup=main_menu_keyboard())

@router.message(F.text == "👤 Profil")
async def profile_handler(message: Message):
    u = await get_user(message.from_user.id)
    if not u: return
    from database.db import get_user_results, get_subscription
    results = await get_user_results(u.telegram_id)
    sub     = await get_subscription(u.telegram_id)
    sub_text = f"✅ {str(sub.expires_at)[:16]} gacha" if sub else "❌ Obuna yo'q"
    await message.answer(
        f"👤 <b>{u.full_name}</b>\n"
        f"📱 {u.phone_number or '—'}\n"
        f"──────────────\n"
        f"💳 Obuna: {sub_text}\n"
        f"📊 Jami testlar: <b>{len(results)}</b>",
        parse_mode="HTML"
    )

@router.message(F.text == "📊 Natijalarim")
async def my_results(message: Message):
    from database.db import get_user_results
    results = await get_user_results(message.from_user.id)
    if not results:
        await message.answer("📊 Hali test topshirmadingiz.")
        return
    SUBJ = {'onatili': '📚', 'adabiyot': '📖'}
    text = "📊 <b>So'nggi natijalar:</b>\n\n"
    for r in results[:10]:
        bolim_txt = f"{r.bolim}-bo'lim" if r.bolim > 0 else "Aralash"
        text += (
            f"{SUBJ.get(r.subject,'📚')} {bolim_txt} | "
            f"✅{r.correct} ❌{r.wrong} | "
            f"<b>{r.score_pct}%</b>\n"
        )
    await message.answer(text, parse_mode="HTML")
