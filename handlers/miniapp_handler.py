import json, logging
from aiogram import Router, F, Bot
from aiogram.types import Message

from database.db import get_user, save_result
from keyboards.keyboards import main_menu_keyboard
from config import config

router = Router()
logger = logging.getLogger(__name__)

def grade(pct: float) -> tuple[str, str]:
    if pct >= 86: return "🏆", "A'lo (70% ustama)"
    if pct >= 80: return "🥇", "Oliy toifa"
    if pct >= 70: return "🥈", "1-toifa"
    if pct >= 60: return "🥉", "2-toifa"
    return "📋", "Mutaxassis"

@router.message(F.web_app_data)
async def receive_result(message: Message, bot: Bot):
    tid      = message.from_user.id
    username = message.from_user.username

    try:
        data = json.loads(message.web_app_data.data)
    except Exception as e:
        logger.error(f"JSON parse xato: {e}")
        await message.answer("❌ Natija o'qishda xato.")
        return

    correct  = int(data.get("correct",  0))
    wrong    = int(data.get("wrong",    0))
    skipped  = int(data.get("skip",     0))
    total    = int(data.get("total",    0))
    pct      = float(data.get("score",  0))
    subject  = data.get("subject",  "onatili")
    bolim    = int(data.get("bolim", 0))
    wrong_ids   = data.get("wrong_ids",   [])
    correct_ids = data.get("correct_ids", [])

    user = await get_user(tid)
    full_name  = user.full_name if user else message.from_user.full_name or "Foydalanuvchi"
    uname_link = f"@{username}" if username else full_name

    emoji, grade_label = grade(pct)
    SUBJ = {"onatili": "📚 Ona tili", "adabiyot": "📖 Adabiyot"}
    subj_label  = SUBJ.get(subject, subject)
    bolim_label = f"{bolim}-bo'lim" if bolim > 0 else "Aralash"

    # Guruhga
    if config.RESULT_GROUP_ID:
        try:
            await bot.send_message(
                chat_id    = int(config.RESULT_GROUP_ID),
                text       = (
                    f"{emoji} <b>{full_name}</b> ({uname_link})\n"
                    f"📌 {subj_label} | {bolim_label}\n"
                    f"✅ {correct}/{total} | 📈 {pct:.0f}% | {grade_label}"
                ),
                parse_mode = "HTML"
            )
        except Exception as e:
            logger.error(f"Guruhga yuborishda xato: {e}")

    # DB ga saqlash
    await save_result(
        telegram_id=tid, subject=subject, bolim=bolim,
        correct=correct, wrong=wrong, skipped=skipped, score_pct=round(pct, 1)
    )

    # Foydalanuvchiga
    encourage = "🌟 Ajoyib natija!" if pct >= 70 else "📖 Ko'proq mashq qiling!"
    await message.answer(
        f"👤 <b>{full_name}</b>\n"
        f"━━━━━━━━━━━━━\n"
        f"📌 {subj_label} | {bolim_label}\n"
        f"━━━━━━━━━━━━━\n"
        f"✅ To'g'ri:     <b>{correct}/{total}</b>\n"
        f"❌ Xato:        <b>{wrong}/{total}</b>\n"
        f"⏭ O'tkazildi: <b>{skipped}</b>\n"
        f"📈 Ball:        <b>{pct:.0f}%</b>\n"
        f"━━━━━━━━━━━━━\n"
        f"{emoji} <b>{grade_label}</b>\n\n"
        f"{encourage}",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )
