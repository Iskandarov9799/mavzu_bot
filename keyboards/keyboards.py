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


# ══════════════════════════════════════════════
# SAVOLLAR MUHARRIRI KEYBOARDLARI
# ══════════════════════════════════════════════

def qedit_page_keyboard(questions: list, page: int, total: int, prefix: str) -> InlineKeyboardMarkup:
    buttons = []
    SUBJ = {"onatili": "📚", "adabiyot": "📖"}
    for q in questions:
        icon     = SUBJ.get(q.subject, "❓")
        bolim_tx = f"[{q.bolim}-b]" if q.bolim > 0 else "[Ar]"
        label    = f"{icon}#{q.id} {bolim_tx} {q.question_text[:25]}…"
        buttons.append([InlineKeyboardButton(
            text          = label,
            callback_data = f"qedit:view:{q.id}:{page}:{prefix}"
        )])
    total_pages = max(1, (total + 5 - 1) // 5)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"qedit:page:{page-1}:{prefix}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="qedit:noop"))
    if (page + 1) * 5 < total:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"qedit:page:{page+1}:{prefix}"))
    if nav:
        buttons.append(nav)
    buttons.append([
        InlineKeyboardButton(text="🔍 Qidirish", callback_data="qedit:search"),
        InlineKeyboardButton(text="❌ Yopish",    callback_data="qedit:close"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def qedit_action_keyboard(qid: int, page: int, prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"qedit:edit:{qid}:{page}:{prefix}"),
            InlineKeyboardButton(text="🗑 O'chirish",  callback_data=f"qedit:del:{qid}:{page}:{prefix}"),
        ],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"qedit:page:{page}:{prefix}")],
    ])

def qedit_fields_keyboard(qid: int, page: int, prefix: str) -> InlineKeyboardMarkup:
    fields = [
        ("question_text",  "📝 Savol matni"),
        ("option_a",       "🅰 A varianti"),
        ("option_b",       "🅱 B varianti"),
        ("option_c",       "🅲 C varianti"),
        ("option_d",       "🅳 D varianti"),
        ("correct_answer", "✅ To'g'ri javob"),
        ("bolim",          "📌 Bo'lim raqami"),
        ("subject",        "📚 Fan (onatili/adabiyot)"),
        ("image_file_id",  "🖼 Rasm ID"),
    ]
    buttons = []
    for fkey, flabel in fields:
        buttons.append([InlineKeyboardButton(
            text          = flabel,
            callback_data = f"qedit:field:{fkey}:{qid}:{page}:{prefix}"
        )])
    buttons.append([InlineKeyboardButton(
        text="🔙 Orqaga", callback_data=f"qedit:view:{qid}:{page}:{prefix}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)