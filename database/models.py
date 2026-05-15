from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime,
    ForeignKey, Integer, String, Text, Numeric
)
from sqlalchemy.orm import DeclarativeBase

def _now():
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id   = Column(BigInteger, unique=True, nullable=False)
    phone_number  = Column(String(20))
    full_name     = Column(String(255))
    username      = Column(String(100))
    is_registered = Column(Boolean, default=False)
    is_banned     = Column(Boolean, default=False)
    registered_at = Column(DateTime(timezone=True), default=_now)

class Question(Base):
    __tablename__ = "questions"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    subject        = Column(String(20), nullable=False)   # onatili | adabiyot
    bolim          = Column(Integer, nullable=False)       # 0=aralash, 1-40
    question_text  = Column(Text, nullable=False)
    option_a       = Column(Text)
    option_b       = Column(Text)
    option_c       = Column(Text)
    option_d       = Column(Text)
    correct_answer = Column(String(1))                    # A B C D
    image_file_id  = Column(String(200))
    order_num      = Column(Integer, default=0)
    created_at     = Column(DateTime(timezone=True), default=_now)

class Subscription(Base):
    __tablename__ = "subscriptions"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    sub_type    = Column(String(20), nullable=False)      # daily | monthly
    expires_at  = Column(DateTime(timezone=True), nullable=False)
    created_at  = Column(DateTime(timezone=True), default=_now)

class Purchase(Base):
    __tablename__ = "purchases"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id  = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    product_type = Column(String(20), nullable=False)
    amount       = Column(Integer, nullable=False)
    check_photo  = Column(String(200))
    status       = Column(String(20), default="pending")
    submitted_at = Column(DateTime(timezone=True), default=_now)
    confirmed_at = Column(DateTime(timezone=True))
    confirmed_by = Column(BigInteger)

class TestResult(Base):
    __tablename__ = "test_results"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    subject     = Column(String(20), nullable=False)
    bolim       = Column(Integer, nullable=False)
    correct     = Column(Integer, default=0)
    wrong       = Column(Integer, default=0)
    skipped     = Column(Integer, default=0)
    score_pct   = Column(Numeric(5, 1), default=0)
    finished_at = Column(DateTime(timezone=True), default=_now)
