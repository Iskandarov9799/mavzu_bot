from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)
from config import config

# ══════════════════════════════════════════════
# REPLY KEYBOARDS
# ══════════════════════════════════════════════

def phone_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamimni ulashish", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )

def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Ona tili"), KeyboardButton(text="📖 Adabiyot")],
            [KeyboardButton(text="📊 Natijalarim"), KeyboardButton(text="👤 Profil")],
        ],
        resize_keyboard=True
    )

def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Kutayotgan to'lovlar")],
            [KeyboardButton(text="👥 Foydalanuvchilar"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="📢 Broadcast"),        KeyboardButton(text="👥 A'zolar")],
            [KeyboardButton(text="➕ Savol qo'shish"),   KeyboardButton(text="📋 Savollar")],
            [KeyboardButton(text="📤 Excel import"),     KeyboardButton(text="📥 Excel eksport")],
            [KeyboardButton(text="🗑 Bo'lim o'chirish"),  KeyboardButton(text="🔗 Yechim linki")],
            [KeyboardButton(text="♻️ Tariflarni nollash")],
            [KeyboardButton(text="🔙 Orqaga")],
        ],
        resize_keyboard=True
    )

def cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )

def skip_image_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏭ Rasmisiz davom etish")],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True
    )

# ══════════════════════════════════════════════
# INLINE KEYBOARDS
# ══════════════════════════════════════════════

def payment_options_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"📅 Kunlik — {config.PRICE_DAILY:,} so'm (24 soat)",
            callback_data="pay:daily"
        )],
        [InlineKeyboardButton(
            text=f"📆 Oylik — {config.PRICE_MONTHLY:,} so'm (30 kun)",
            callback_data="pay:monthly"
        )],
        [InlineKeyboardButton(text="❌ Bekor", callback_data="pay:cancel")],
    ])

def payment_confirm_keyboard(purchase_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm_pay:{purchase_id}"),
        InlineKeyboardButton(text="❌ Rad etish",  callback_data=f"reject_pay:{purchase_id}"),
    ]])

def inline_cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="pay:cancel")]
    ])

async def bolimlar_keyboard(subject: str) -> InlineKeyboardMarkup:
    """Bo'limlar klaviaturasi — savollar borligini DB dan tekshiradi."""
    from database.db import count_questions
    buttons = []

    # Aralash tugmasi
    cnt_all = await count_questions(subject=subject, bolim=0)
    buttons.append([InlineKeyboardButton(
        text=f"🔀 Aralash (barcha bo'limlar)" if cnt_all > 0 else "🔀 Aralash — ⏳",
        callback_data=f"test:{subject}:0"
    )])

    # 1-40 bo'limlar (2 qatordan)
    row = []
    for i in range(1, config.BOLIMLAR_COUNT + 1):
        cnt = await count_questions(subject=subject, bolim=i)
        icon = "📋" if cnt > 0 else "⏳"
        row.append(InlineKeyboardButton(
            text=f"{icon} {i}",
            callback_data=f"test:{subject}:{i}"
        ))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def member_action_keyboard(telegram_id: int, is_banned: bool):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Blokni ochish" if is_banned else "🚫 Bloklash",
            callback_data=f"member:ban:{telegram_id}"
        )],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="members:back")],
    ])

def correct_answer_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="A", callback_data="addq:correct:A"),
        InlineKeyboardButton(text="B", callback_data="addq:correct:B"),
        InlineKeyboardButton(text="C", callback_data="addq:correct:C"),
        InlineKeyboardButton(text="D", callback_data="addq:correct:D"),
    ]])

def subject_select_keyboard(prefix: str = "addq:subject"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Ona tili",  callback_data=f"{prefix}:onatili")],
        [InlineKeyboardButton(text="📖 Adabiyot",  callback_data=f"{prefix}:adabiyot")],
        [InlineKeyboardButton(text="❌ Bekor",      callback_data="addq:cancel")],
    ])

def bolim_select_keyboard(subject: str, prefix: str = "addq:bolim"):
    """Admin uchun bo'lim tanlash (0-40)"""
    buttons = []
    buttons.append([InlineKeyboardButton(
        text="0 — Aralash (bo'limsiz)",
        callback_data=f"{prefix}:{subject}:0"
    )])
    row = []
    for i in range(1, config.BOLIMLAR_COUNT + 1):
        row.append(InlineKeyboardButton(
            text=str(i),
            callback_data=f"{prefix}:{subject}:{i}"
        ))
        if len(row) == 5:
            buttons.append(row); row = []
    if row: buttons.append(row)
    buttons.append([InlineKeyboardButton(text="❌ Bekor", callback_data="addq:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
