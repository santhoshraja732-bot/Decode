from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_admin
from ..audit import log_action

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------- Transactions oversight ----------------
@router.get("/transactions", response_model=List[schemas.TransactionOut])
def list_all_transactions(
    status_filter: Optional[models.TransactionStatus] = Query(None, alias="status"),
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    q = db.query(models.Transaction)
    if status_filter:
        q = q.filter(models.Transaction.status == status_filter)
    return q.order_by(models.Transaction.created_at.desc()).all()


@router.post("/transactions/{transaction_id}/decision", response_model=schemas.TransactionOut)
def decide_transaction(
    transaction_id: str,
    payload: schemas.AdminTransactionDecision,
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    txn = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if txn.status not in (models.TransactionStatus.FLAGGED, models.TransactionStatus.HELD, models.TransactionStatus.BLOCKED):
        raise HTTPException(status_code=400, detail="Only flagged, held, or blocked transactions can be reviewed")

    sender = db.query(models.User).filter(models.User.id == txn.sender_id).first()

    # FLAGGED transactions already had funds deducted at creation time (they're
    # "allowed through but watched"). HELD/BLOCKED transactions never touched
    # the balance. Track this so approve/reject/block move money correctly
    # instead of double-deducting or silently losing funds on a reject.
    already_deducted = txn.status == models.TransactionStatus.FLAGGED

    if payload.decision == "approve":
        if not already_deducted:
            if txn.amount > sender.balance:
                raise HTTPException(status_code=400, detail="Sender no longer has sufficient balance")
            sender.balance -= txn.amount
        txn.status = models.TransactionStatus.COMPLETED
    elif payload.decision == "reject":
        if already_deducted:
            sender.balance += txn.amount  # refund — the transaction never actually completed
        txn.status = models.TransactionStatus.REJECTED
    elif payload.decision == "block":
        if already_deducted:
            sender.balance += txn.amount  # refund — blocked means it did not go through
        txn.status = models.TransactionStatus.BLOCKED
    else:
        raise HTTPException(status_code=400, detail="decision must be 'approve', 'reject', or 'block'")

    db.commit()
    db.refresh(txn)

    log_action(
        db, admin, f"ADMIN_TRANSACTION_{payload.decision.upper()}", "transaction", txn.id,
        payload.note or f"Admin {admin.username} set decision '{payload.decision}'."
    )
    return txn


# ---------------- Suspicious activity ----------------
@router.get("/suspicious-activities", response_model=List[schemas.SuspiciousActivityOut])
def list_suspicious_activities(
    resolved: Optional[bool] = None,
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    q = db.query(models.SuspiciousActivity)
    if resolved is not None:
        q = q.filter(models.SuspiciousActivity.resolved == resolved)
    return q.order_by(models.SuspiciousActivity.created_at.desc()).all()


@router.post("/suspicious-activities/{activity_id}/resolve", response_model=schemas.SuspiciousActivityOut)
def resolve_activity(
    activity_id: str,
    payload: schemas.ResolveActivity,
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    activity = db.query(models.SuspiciousActivity).filter(models.SuspiciousActivity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Suspicious activity not found")
    activity.resolved = True
    activity.resolution_note = payload.resolution_note
    db.commit()
    db.refresh(activity)

    log_action(db, admin, "SUSPICIOUS_ACTIVITY_RESOLVED", "suspicious_activity", activity.id, payload.resolution_note)
    return activity


# ---------------- User management ----------------
@router.get("/users", response_model=List[schemas.UserOut])
def list_users(admin: models.User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return db.query(models.User).order_by(models.User.created_at.desc()).all()


@router.post("/users/{user_id}/status", response_model=schemas.UserOut)
def update_user_status(
    user_id: str,
    payload: schemas.UserAdminUpdate,
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_blocked = payload.is_blocked
    if not payload.is_blocked:
        user.failed_otp_streak = 0
    db.commit()
    db.refresh(user)

    action = "USER_BLOCKED" if payload.is_blocked else "USER_UNBLOCKED"
    log_action(db, admin, action, "user", user.id, f"By admin {admin.username}")
    return user


# ---------------- Blacklist management ----------------
@router.get("/blacklist")
def list_blacklist(admin: models.User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return db.query(models.BlacklistedAccount).order_by(models.BlacklistedAccount.created_at.desc()).all()


@router.post("/blacklist")
def add_to_blacklist(
    account_number: str,
    reason: Optional[str] = None,
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if db.query(models.BlacklistedAccount).filter(models.BlacklistedAccount.account_number == account_number).first():
        raise HTTPException(status_code=400, detail="Account already blacklisted")
    entry = models.BlacklistedAccount(account_number=account_number, reason=reason)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    log_action(db, admin, "ACCOUNT_BLACKLISTED", "blacklist", entry.id, reason)
    return entry


@router.delete("/blacklist/{entry_id}")
def remove_from_blacklist(
    entry_id: str,
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    entry = db.query(models.BlacklistedAccount).filter(models.BlacklistedAccount.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()
    log_action(db, admin, "ACCOUNT_UNBLACKLISTED", "blacklist", entry_id, None)
    return {"message": "Removed"}


# ---------------- Audit logs ----------------
@router.get("/audit-logs", response_model=List[schemas.AuditLogOut])
def list_audit_logs(
    limit: int = Query(200, le=1000),
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.AuditLog)
        .order_by(models.AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )


# ---------------- Dashboard stats ----------------
@router.get("/stats", response_model=schemas.DashboardStats)
def dashboard_stats(admin: models.User = Depends(get_current_admin), db: Session = Depends(get_db)):
    total_users = db.query(models.User).count()
    total_txns = db.query(models.Transaction).count()
    completed = db.query(models.Transaction).filter(models.Transaction.status == models.TransactionStatus.COMPLETED).count()
    flagged = db.query(models.Transaction).filter(models.Transaction.status == models.TransactionStatus.FLAGGED).count()
    held = db.query(models.Transaction).filter(models.Transaction.status == models.TransactionStatus.HELD).count()
    blocked = db.query(models.Transaction).filter(models.Transaction.status == models.TransactionStatus.BLOCKED).count()
    total_sa = db.query(models.SuspiciousActivity).count()
    unresolved_sa = db.query(models.SuspiciousActivity).filter(models.SuspiciousActivity.resolved == False).count()  # noqa: E712

    return schemas.DashboardStats(
        total_users=total_users,
        total_transactions=total_txns,
        completed_transactions=completed,
        flagged_transactions=flagged,
        held_transactions=held,
        blocked_transactions=blocked,
        total_suspicious_activities=total_sa,
        unresolved_suspicious_activities=unresolved_sa,
    )
