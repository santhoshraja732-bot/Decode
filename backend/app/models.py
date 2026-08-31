"""
ORM models for users, wallets, transactions, OTPs, suspicious activity
flags, audit logs, and blacklisted accounts/devices.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, ForeignKey,
    Enum, Text
)
from sqlalchemy.orm import relationship

from .database import Base


def gen_id():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class TransactionStatus(str, enum.Enum):
    PENDING_OTP = "pending_otp"     # awaiting OTP verification
    PROCESSING = "processing"       # OTP verified, running fraud checks
    COMPLETED = "completed"         # passed checks, simulated as settled
    FLAGGED = "flagged"             # suspicious, held for admin review
    HELD = "held"                   # explicitly put on hold by a rule/admin
    BLOCKED = "blocked"             # auto-blocked or admin-blocked
    REJECTED = "rejected"           # admin rejected after review
    FAILED = "failed"               # OTP failed / cancelled


class Severity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    balance = Column(Float, default=50000.0)  # simulated wallet balance
    is_blocked = Column(Boolean, default=False)
    failed_otp_streak = Column(Integer, default=0)
    account_number = Column(String, unique=True, default=lambda: uuid.uuid4().hex[:12])
    created_at = Column(DateTime, default=datetime.utcnow)

    sent_transactions = relationship(
        "Transaction", foreign_keys="Transaction.sender_id", back_populates="sender"
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=gen_id)
    sender_id = Column(String, ForeignKey("users.id"), nullable=False)
    receiver_account = Column(String, nullable=False)  # simulated receiver account no.
    receiver_name = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING_OTP)
    risk_score = Column(Integer, default=0)  # 0-100
    flag_reasons = Column(Text, default="")  # comma-separated / newline separated
    device_id = Column(String, nullable=True)   # simulated device fingerprint
    ip_address = Column(String, nullable=True)  # simulated IP
    otp_required = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_transactions")
    otps = relationship("OTP", back_populates="transaction")


class OTP(Base):
    __tablename__ = "otps"

    id = Column(String, primary_key=True, default=gen_id)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    code = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    verified = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("Transaction", back_populates="otps")


class SuspiciousActivity(Base):
    __tablename__ = "suspicious_activities"

    id = Column(String, primary_key=True, default=gen_id)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    rule_triggered = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(Enum(Severity), default=Severity.MEDIUM)
    resolved = Column(Boolean, default=False)
    resolution_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=gen_id)
    actor_id = Column(String, ForeignKey("users.id"), nullable=True)
    actor_username = Column(String, nullable=True)
    action = Column(String, nullable=False)
    target_type = Column(String, nullable=True)
    target_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class BlacklistedAccount(Base):
    __tablename__ = "blacklisted_accounts"

    id = Column(String, primary_key=True, default=gen_id)
    account_number = Column(String, unique=True, nullable=False)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class KnownDevice(Base):
    """Tracks devices previously used by a user, to detect new-device risk."""
    __tablename__ = "known_devices"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    device_id = Column(String, nullable=False)
    first_seen = Column(DateTime, default=datetime.utcnow)
