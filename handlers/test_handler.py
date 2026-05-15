import json, base64, zlib, logging, os, hashlib
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)

from database.db import (
    is_registered, has_subscription,
    get_questions, count_questions
)
from keyboards.keyboards import (
    main_menu_keyboard, bolimlar_keyboard, payment_options_keyboard
)
from config import config

router = Router()
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════
# ENCODING
# ══════════════════════════════════════════════

def encode_questions(q_list: list, meta: dict) -> str:
    payload = {'meta': meta, 'questions': q_list}
    raw = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    return base64.urlsafe_b64encode(zlib.compress(raw.encode(), level=9)).decode()

def questions_to_miniapp(questions: list) -> list:
    return [{
        "id":  q.id,
        "t":   q.question_text,
        "a":   q.option_a or "",
        "b":   q.option_b or "",
        "c":   q.option_c or "",
        "d":   q.option_d or "",
        "ok":  q.correct_answer or "",
        "img": q.image_file_id or "",
    } for q in questions]

async def resolve_images(q_list: list, bot) -> list:
    result = []
    for q in q_list:
        img = q.get("img", "")
        if not img or img.startswith("http"):
            result.append(q); continue
        images_url = config.IMAGES_URL
        images_dir = config.IMAGES_DIR
        if images_url and images_dir:
            fname = hashlib.md5(img.encode()).hexdigest() + ".jpg"
            fpath = os.path.join(images_dir, fname)
            if os.path.exists(fpath):
                q = {**q, "img": f"{images_url.rstrip('/')}/{fname}"}
                result.append(q); continue
        try:
            file = await bot.get_file(img)
            url  = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
            q    = {**q, "img": url}
        except Exception:
            q = {**q, "img": ""}
        result.append(q)
    return result

def make_test_kb(url: str, label: str = "🚀 Testni boshlash") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, web_app=WebAppInfo(url=url))]
    ])

# ══════════════════════════════════════════════
# MENYU
# ══════════════════════════════════════════════

@router.message(F.text.in_(["📚 Ona tili", "📖 Adabiyot"]))
async def subject_menu(message: Message):
    if not await is_registered(message.from_user.id):
        await message.answer("❗ Avval /start orqali ro'yxatdan o'ting.")
        return
    subject = "onatili" if "Ona tili" in message.text else "adabiyot"
    SUBJ    = {"onatili": "📚 Ona tili", "adabiyot": "📖 Adabiyot"}
    kb = await bolimlar_keyboard(subject)
    await message.answer(
        f"{SUBJ[subject]}\n\nBo'limni tanlang:\n"
        f"<i>📋 — savollar bor | ⏳ — hali qo'shilmagan</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )

# ══════════════════════════════════════════════
# TEST BOSHLASH
# ══════════════════════════════════════════════

@router.callback_query(F.data.startswith("test:"))
async def start_test(callback: CallbackQuery):
    parts   = callback.data.split(":")
    subject = parts[1]
    bolim   = int(parts[2])
    tid     = callback.from_user.id

    # Savol borligini tekshirish
    cnt = await count_questions(subject=subject, bolim=bolim)
    if cnt == 0:
        await callback.answer(
            "⏳ Bu bo'limda hali savollar qo'shilmagan.\nAdminni kutib turing.",
            show_alert=True
        )
        return

    # Obuna tekshirish
    if not await has_subscription(tid):
        SUBJ = {"onatili": "📚 Ona tili", "adabiyot": "📖 Adabiyot"}
        bolim_txt = f"{bolim}-bo'lim" if bolim > 0 else "Aralash"
        try:
            await callback.message.edit_text(
                f"{SUBJ[subject]} — <b>{bolim_txt}</b>\n\n"
                f"🔒 Bu bo'limga kirish uchun obuna kerak.\n\n"
                f"To'lov turini tanlang:",
                reply_markup=payment_options_keyboard(),
                parse_mode="HTML"
            )
        except Exception:
            await callback.message.answer(
                f"🔒 Obuna kerak. To'lov turini tanlang:",
                reply_markup=payment_options_keyboard()
            )
        await callback.answer()
        return

    # Savollarni olish
    questions = await get_questions(subject=subject, bolim=bolim, count=config.MAX_QUESTIONS)
    if not questions:
        await callback.answer("❌ Savollar topilmadi!", show_alert=True)
        return

    q_list  = questions_to_miniapp(questions)
    q_list  = await resolve_images(q_list, callback.bot)
    bolim_label = f"{bolim}-bo'lim" if bolim > 0 else "Aralash"
    meta = {
        "subject":      subject,
        "bolim":        bolim,
        "bolim_label":  bolim_label,
        "solution_url": config.SOLUTION_URL,
    }
    encoded = encode_questions(q_list, meta)
    url     = f"{config.MINI_APP_URL.rstrip('/')}/?data={encoded}"

    kb = make_test_kb(url, f"🚀 {bolim_label} testini boshlash")
    SUBJ = {"onatili": "📚 Ona tili", "adabiyot": "📖 Adabiyot"}
    text = (
        f"{SUBJ[subject]} — <b>{bolim_label}</b>\n\n"
        f"📊 Savollar: <b>{len(questions)} ta</b>\n\n"
        f"Testni boshlash uchun tugmani bosing 👇"
    )
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        try: await callback.message.delete()
        except Exception: pass
        await callback.bot.send_message(
            chat_id=tid, text=text, reply_markup=kb, parse_mode="HTML"
        )
    await callback.answer()

@router.callback_query(F.data == "back:main")
async def back_main(callback: CallbackQuery):
    try: await callback.message.delete()
    except Exception: pass
    await callback.answer()
