import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.db import (
    create_purchase, confirm_purchase, reject_purchase,
    get_purchase_by_id, get_pending_purchases, get_user, grant_subscription
)
from keyboards.keyboards import (
    inline_cancel_keyboard, payment_confirm_keyboard, main_menu_keyboard
)
from states import PaymentStates
from config import config

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data.startswith("pay:"))
async def pay_start(callback: CallbackQuery, state: FSMContext):
    pay_type = callback.data.split(":")[1]
    if pay_type == "cancel":
        await state.clear()
        try: await callback.message.edit_reply_markup(reply_markup=None)
        except Exception: pass
        await callback.message.answer("❌ Bekor qilindi.", reply_markup=main_menu_keyboard())
        await callback.answer()
        return

    amount = config.PRICE_DAILY if pay_type == "daily" else config.PRICE_MONTHLY
    label  = f"Kunlik (24 soat)" if pay_type == "daily" else f"Oylik (30 kun)"

    await state.update_data(pay_type=pay_type, amount=amount)
    await callback.message.edit_text(
        f"💳 <b>{label} — {amount:,} so'm</b>\n\n"
        f"Kartaga o'tkazing:\n"
        f"<code>{config.PAYMENT_CARD}</code>\n"
        f"<b>{config.PAYMENT_OWNER}</b>\n\n"
        f"Chek rasmini yuboring 👇",
        reply_markup=inline_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(PaymentStates.waiting_for_check)
    await callback.answer()

@router.message(PaymentStates.waiting_for_check, F.photo)
async def receive_check(message: Message, state: FSMContext, bot: Bot):
    data     = await state.get_data()
    pay_type = data.get("pay_type", "daily")
    amount   = data.get("amount", config.PRICE_DAILY)
    await state.clear()

    file_id     = message.photo[-1].file_id
    purchase_id = await create_purchase(
        telegram_id=message.from_user.id,
        product_type=pay_type, amount=amount, check_photo=file_id
    )

    await message.answer(
        "✅ <b>Chekingiz qabul qilindi!</b>\n\n⏳ Admin tez orada aktivlashtiradi.",
        reply_markup=main_menu_keyboard(), parse_mode="HTML"
    )

    user  = await get_user(message.from_user.id)
    uname = f"@{user.username}" if user and user.username else str(message.from_user.id)
    label = "Kunlik" if pay_type == "daily" else "Oylik"

    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_photo(
                chat_id      = admin_id,
                photo        = file_id,
                caption      = (
                    f"💰 <b>Yangi to'lov #{purchase_id}</b>\n\n"
                    f"👤 {user.full_name if user else '?'} | {uname}\n"
                    f"📦 {label} — {amount:,} so'm"
                ),
                reply_markup = payment_confirm_keyboard(purchase_id),
                parse_mode   = "HTML"
            )
        except Exception as e:
            logger.error(f"Admin ga yuborishda xato: {e}")

@router.message(PaymentStates.waiting_for_check)
async def check_not_photo(message: Message):
    if message.text and "Bekor" in message.text:
        return
    await message.answer("📸 Iltimos, <b>rasm</b> (chek) yuboring.", parse_mode="HTML")

@router.callback_query(F.data.startswith("confirm_pay:"))
async def confirm_payment(callback: CallbackQuery, bot: Bot):
    purchase_id = int(callback.data.split(":")[1])
    purchase    = await get_purchase_by_id(purchase_id)
    if not purchase:
        await callback.answer("❌ Topilmadi!"); return

    await confirm_purchase(purchase_id, callback.from_user.id)
    await grant_subscription(purchase.telegram_id, purchase.product_type)

    label = "Kunlik (24 soat)" if purchase.product_type == "daily" else "Oylik (30 kun)"
    try:
        await bot.send_message(
            chat_id      = purchase.telegram_id,
            text         = f"✅ <b>To'lovingiz tasdiqlandi!</b>\n\n🎉 {label} obuna faollashtirildi.",
            reply_markup = main_menu_keyboard(),
            parse_mode   = "HTML"
        )
    except Exception: pass

    try:
        await callback.message.edit_caption(
            caption      = (callback.message.caption or "") + "\n\n✅ <b>TASDIQLANDI</b>",
            reply_markup = None, parse_mode="HTML"
        )
    except Exception: pass
    await callback.answer("✅ Tasdiqlandi!")

@router.callback_query(F.data.startswith("reject_pay:"))
async def reject_payment(callback: CallbackQuery, bot: Bot):
    purchase_id = int(callback.data.split(":")[1])
    purchase    = await get_purchase_by_id(purchase_id)
    if not purchase:
        await callback.answer("❌ Topilmadi!"); return

    await reject_purchase(purchase_id, callback.from_user.id)
    try:
        await bot.send_message(
            purchase.telegram_id,
            "❌ <b>To'lovingiz rad etildi.</b>\nAdmin bilan bog'laning.",
            parse_mode="HTML"
        )
    except Exception: pass

    try:
        await callback.message.edit_caption(
            caption=(callback.message.caption or "") + "\n\n❌ <b>RAD ETILDI</b>",
            reply_markup=None, parse_mode="HTML"
        )
    except Exception: pass
    await callback.answer("❌ Rad etildi.")

@router.message(F.text == "💰 Kutayotgan to'lovlar")
async def pending_payments(message: Message):
    if message.from_user.id not in config.ADMIN_IDS: return
    purchases = await get_pending_purchases()
    if not purchases:
        await message.answer("✅ Kutayotgan to'lovlar yo'q."); return
    for p, user in purchases:
        uname = f"@{user.username}" if user and user.username else str(p.telegram_id)
        label = "Kunlik" if p.product_type == "daily" else "Oylik"
        await message.bot.send_photo(
            chat_id      = message.from_user.id,
            photo        = p.check_photo,
            caption      = (
                f"💰 <b>To'lov #{p.id}</b>\n"
                f"👤 {user.full_name if user else '?'} | {uname}\n"
                f"📦 {label} — {p.amount:,} so'm\n"
                f"🕐 {str(p.submitted_at)[:16]}"
            ),
            reply_markup = payment_confirm_keyboard(p.id),
            parse_mode   = "HTML"
        )
