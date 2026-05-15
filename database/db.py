import os, json, hashlib
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, update, delete, func
from database.models import User, Question, Subscription, Purchase, TestResult
import database.connection as _conn
from config import config

def _now():
    return datetime.now(timezone.utc)

# ══════════════════════════════════════════════
# USERS
# ══════════════════════════════════════════════

async def get_user(telegram_id: int):
    async with _conn.AsyncSessionLocal() as s:
        r = await s.execute(select(User).where(User.telegram_id == telegram_id))
        return r.scalar_one_or_none()

async def create_user(telegram_id: int, full_name: str, username: str = None):
    async with _conn.AsyncSessionLocal() as s:
        ex = await s.execute(select(User).where(User.telegram_id == telegram_id))
        if ex.scalar_one_or_none(): return
        s.add(User(telegram_id=telegram_id, full_name=full_name, username=username))
        await s.commit()

async def update_user_phone(telegram_id: int, phone: str):
    async with _conn.AsyncSessionLocal() as s:
        await s.execute(
            update(User).where(User.telegram_id == telegram_id)
            .values(phone_number=phone, is_registered=True)
        )
        await s.commit()

async def is_registered(telegram_id: int) -> bool:
    u = await get_user(telegram_id)
    return bool(u and u.is_registered)

async def is_banned(telegram_id: int) -> bool:
    u = await get_user(telegram_id)
    return bool(u and u.is_banned)

async def ban_user(telegram_id: int):
    async with _conn.AsyncSessionLocal() as s:
        await s.execute(update(User).where(User.telegram_id == telegram_id).values(is_banned=True))
        await s.commit()

async def unban_user(telegram_id: int):
    async with _conn.AsyncSessionLocal() as s:
        await s.execute(update(User).where(User.telegram_id == telegram_id).values(is_banned=False))
        await s.commit()

async def get_all_users(limit: int = 1000):
    async with _conn.AsyncSessionLocal() as s:
        r = await s.execute(select(User).order_by(User.registered_at.desc()).limit(limit))
        return r.scalars().all()

async def get_users_count() -> int:
    async with _conn.AsyncSessionLocal() as s:
        r = await s.execute(select(func.count()).select_from(User))
        return r.scalar() or 0

# ══════════════════════════════════════════════
# SUBSCRIPTION
# ══════════════════════════════════════════════

async def has_subscription(telegram_id: int) -> bool:
    async with _conn.AsyncSessionLocal() as s:
        r = await s.execute(
            select(Subscription).where(
                Subscription.telegram_id == telegram_id,
                Subscription.expires_at > _now()
            )
        )
        return r.scalar_one_or_none() is not None

async def grant_subscription(telegram_id: int, sub_type: str):
    days = 1 if sub_type == "daily" else 30
    expires = _now() + timedelta(days=days)
    async with _conn.AsyncSessionLocal() as s:
        r = await s.execute(
            select(Subscription).where(Subscription.telegram_id == telegram_id)
        )
        sub = r.scalar_one_or_none()
        if sub:
            if sub.expires_at > _now():
                sub.expires_at += timedelta(days=days)
            else:
                sub.expires_at = expires
        else:
            s.add(Subscription(
                telegram_id=telegram_id, sub_type=sub_type, expires_at=expires
            ))
        await s.commit()

async def get_subscription(telegram_id: int):
    async with _conn.AsyncSessionLocal() as s:
        r = await s.execute(
            select(Subscription).where(
                Subscription.telegram_id == telegram_id,
                Subscription.expires_at > _now()
            )
        )
        return r.scalar_one_or_none()

async def reset_all_subscriptions():
    async with _conn.AsyncSessionLocal() as s:
        await s.execute(delete(Subscription))
        await s.commit()

# ══════════════════════════════════════════════
# QUESTIONS
# ══════════════════════════════════════════════

async def get_questions(subject: str, bolim: int, count: int = 50):
    """bolim=0 → barcha bo'limlardan aralash"""
    async with _conn.AsyncSessionLocal() as s:
        q = select(Question).where(Question.subject == subject)
        if bolim > 0:
            q = q.where(Question.bolim == bolim)
        q = q.order_by(func.random()).limit(count)
        r = await s.execute(q)
        return r.scalars().all()

async def count_questions(subject: str = None, bolim: int = None) -> int:
    async with _conn.AsyncSessionLocal() as s:
        q = select(func.count()).select_from(Question)
        filters = []
        if subject: filters.append(Question.subject == subject)
        if bolim is not None and bolim >= 0:
            if bolim > 0:
                filters.append(Question.bolim == bolim)
        if filters:
            q = q.where(*filters)
        r = await s.execute(q)
        return r.scalar() or 0

async def add_question(subject: str, bolim: int, text: str,
                       a: str, b: str, c: str, d: str,
                       correct: str, image_id: str = None) -> int:
    async with _conn.AsyncSessionLocal() as s:
        q = Question(
            subject=subject, bolim=bolim,
            question_text=text,
            option_a=a, option_b=b, option_c=c, option_d=d,
            correct_answer=correct.upper(),
            image_file_id=image_id
        )
        s.add(q)
        await s.commit()
        await s.refresh(q)
        return q.id

async def delete_question(qid: int):
    async with _conn.AsyncSessionLocal() as s:
        await s.execute(delete(Question).where(Question.id == qid))
        await s.commit()

async def delete_bolim_questions(subject: str, bolim: int):
    async with _conn.AsyncSessionLocal() as s:
        await s.execute(
            delete(Question).where(
                Question.subject == subject,
                Question.bolim == bolim
            )
        )
        await s.commit()

async def get_question_by_id(qid: int):
    async with _conn.AsyncSessionLocal() as s:
        r = await s.execute(select(Question).where(Question.id == qid))
        return r.scalar_one_or_none()

async def update_question(qid: int, **kwargs):
    async with _conn.AsyncSessionLocal() as s:
        await s.execute(update(Question).where(Question.id == qid).values(**kwargs))
        await s.commit()

async def get_questions_page(subject: str = None, offset: int = 0, limit: int = 10):
    async with _conn.AsyncSessionLocal() as s:
        q = select(Question)
        if subject:
            q = q.where(Question.subject == subject)
        q = q.order_by(Question.subject, Question.bolim, Question.id).offset(offset).limit(limit)
        r = await s.execute(q)
        return r.scalars().all()

async def search_questions(keyword: str, limit: int = 20):
    async with _conn.AsyncSessionLocal() as s:
        r = await s.execute(
            select(Question)
            .where(Question.question_text.ilike(f"%{keyword}%"))
            .limit(limit)
        )
        return r.scalars().all()

async def import_questions_from_excel(rows: list) -> tuple[int, list]:
    """Excel dan savollarni import qilish.
    rows: [{'subject','bolim','text','a','b','c','d','correct','image'}]
    """
    added  = 0
    errors = []
    async with _conn.AsyncSessionLocal() as s:
        for i, row in enumerate(rows, 1):
            try:
                subject = str(row.get('subject', '')).strip().lower()
                if subject not in ('onatili', 'adabiyot'):
                    errors.append(f"Qator {i}: subject noto'g'ri '{subject}'")
                    continue
                bolim = int(row.get('bolim', 0))
                text  = str(row.get('text', '')).strip()
                if not text:
                    errors.append(f"Qator {i}: savol matni bo'sh")
                    continue
                correct = str(row.get('correct', '')).strip().upper()
                if correct not in ('A', 'B', 'C', 'D'):
                    errors.append(f"Qator {i}: correct '{correct}' noto'g'ri")
                    continue
                s.add(Question(
                    subject=subject, bolim=bolim,
                    question_text=text,
                    option_a=str(row.get('a', '')).strip(),
                    option_b=str(row.get('b', '')).strip(),
                    option_c=str(row.get('c', '')).strip(),
                    option_d=str(row.get('d', '')).strip(),
                    correct_answer=correct,
                    image_file_id=row.get('image') or None
                ))
                added += 1
            except Exception as e:
                errors.append(f"Qator {i}: {e}")
        await s.commit()
    return added, errors

# ══════════════════════════════════════════════
# PURCHASE
# ══════════════════════════════════════════════

async def create_purchase(telegram_id: int, product_type: str, amount: int, check_photo: str) -> int:
    async with _conn.AsyncSessionLocal() as s:
        p = Purchase(
            telegram_id=telegram_id, product_type=product_type,
            amount=amount, check_photo=check_photo
        )
        s.add(p)
        await s.commit()
        await s.refresh(p)
        return p.id

async def confirm_purchase(purchase_id: int, admin_id: int):
    async with _conn.AsyncSessionLocal() as s:
        r = await s.execute(select(Purchase).where(Purchase.id == purchase_id))
        p = r.scalar_one_or_none()
        if p:
            p.status = "confirmed"
            p.confirmed_at = _now()
            p.confirmed_by = admin_id
            await s.commit()

async def reject_purchase(purchase_id: int, admin_id: int):
    async with _conn.AsyncSessionLocal() as s:
        r = await s.execute(select(Purchase).where(Purchase.id == purchase_id))
        p = r.scalar_one_or_none()
        if p:
            p.status = "rejected"
            p.confirmed_by = admin_id
            await s.commit()

async def get_purchase_by_id(purchase_id: int):
    async with _conn.AsyncSessionLocal() as s:
        r = await s.execute(select(Purchase).where(Purchase.id == purchase_id))
        return r.scalar_one_or_none()

async def get_pending_purchases():
    async with _conn.AsyncSessionLocal() as s:
        r = await s.execute(
            select(Purchase, User)
            .join(User, Purchase.telegram_id == User.telegram_id)
            .where(Purchase.status == "pending")
            .order_by(Purchase.submitted_at)
        )
        return r.all()

# ══════════════════════════════════════════════
# TEST RESULTS
# ══════════════════════════════════════════════

async def save_result(telegram_id: int, subject: str, bolim: int,
                      correct: int, wrong: int, skipped: int, score_pct: float):
    async with _conn.AsyncSessionLocal() as s:
        s.add(TestResult(
            telegram_id=telegram_id, subject=subject, bolim=bolim,
            correct=correct, wrong=wrong, skipped=skipped, score_pct=score_pct
        ))
        await s.commit()

async def get_user_results(telegram_id: int):
    async with _conn.AsyncSessionLocal() as s:
        r = await s.execute(
            select(TestResult)
            .where(TestResult.telegram_id == telegram_id)
            .order_by(TestResult.finished_at.desc())
            .limit(20)
        )
        return r.scalars().all()

async def get_full_stats():
    async with _conn.AsyncSessionLocal() as s:
        users    = (await s.execute(select(func.count()).select_from(User).where(User.is_registered == True))).scalar() or 0
        qs       = (await s.execute(select(func.count()).select_from(Question))).scalar() or 0
        results  = (await s.execute(select(func.count()).select_from(TestResult))).scalar() or 0
        pending  = (await s.execute(
            select(func.count()).select_from(Purchase).where(Purchase.status == "pending")
        )).scalar() or 0
        return {"users": users, "questions": qs, "results": results, "pending": pending}
