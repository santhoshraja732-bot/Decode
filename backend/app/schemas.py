from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

from .models import UserRole, TransactionStatus, Severity


# ---------- Auth / Users ----------
class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: str
    username: str
    email: str
    role: UserRole
    balance: float
    is_blocked: bool
    account_number: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class DirectoryEntry(BaseModel):
    account_number: str
    username: str


# ---------- Transactions ----------
class TransactionCreate(BaseModel):
    receiver_account: str
    receiver_name: Optional[str] = None
    amount: float = Field(gt=0)
    currency: str = "INR"
    device_id: Optional[str] = "web-default-device"
    ip_address: Optional[str] = "127.0.0.1"


class TransactionOut(BaseModel):
    id: str
    sender_id: str
    receiver_account: str
    receiver_name: Optional[str]
    amount: float
    currency: str
    status: TransactionStatus
    risk_score: int
    flag_reasons: str
    otp_required: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OTPVerify(BaseModel):
    transaction_id: str
    code: str


class OTPRequestOut(BaseModel):
    message: str
    transaction_id: str
    expires_in_seconds: int
    debug_otp: Optional[str] = None  # exposed only because this is a simulation


# ---------- Suspicious Activity / Audit ----------
class SuspiciousActivityOut(BaseModel):
    id: str
    transaction_id: Optional[str]
    user_id: Optional[str]
    rule_triggered: str
    description: str
    severity: Severity
    resolved: bool
    resolution_note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ResolveActivity(BaseModel):
    resolution_note: Optional[str] = None
    approve_transaction: Optional[bool] = None  # if set, also update linked transaction


class AuditLogOut(BaseModel):
    id: str
    actor_id: Optional[str]
    actor_username: Optional[str]
    action: str
    target_type: Optional[str]
    target_id: Optional[str]
    details: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


class AdminTransactionDecision(BaseModel):
    decision: str  # "approve" | "reject" | "block"
    note: Optional[str] = None


class UserAdminUpdate(BaseModel):
    is_blocked: bool


class DashboardStats(BaseModel):
    total_users: int
    total_transactions: int
    completed_transactions: int
    flagged_transactions: int
    held_transactions: int
    blocked_transactions: int
    total_suspicious_activities: int
    unresolved_suspicious_activities: int
