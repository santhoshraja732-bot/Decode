import random
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user
from ..audit import log_action
from ..fraud_rules import evaluate_transaction, status_from_score

router = APIRouter(prefix="/transactions", tags=["transactions"])

OTP_TTL_SECONDS = 120
OTP_MAX_ATTEMPTS = 3
USER_OTP_LOCK_STREAK = 5  # consecutive failures across transactions -> block account


def _generate_otp_code() -> str:
    return f"{random.randint(0, 999999):06d}"


@router.post("/", response_model=schemas.OTPRequestOut, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: schemas.TransactionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if payload.amount > current_user.balance:
        raise HTTPException(status_code=400, detail="Insufficient balance for this transaction")

    if payload.receiver_account == current_user.account_number:
        # Allowed to proceed (self-transfer rule will flag/score it), just a heads-up isn't required here.
        pass

    txn = models.Transaction(
        sender_id=current_user.id,
        receiver_account=payload.receiver_account,
        receiver_name=payload.receiver_name,
        amount=payload.amount,
        currency=payload.currency,
        status=models.TransactionStatus.PENDING_OTP,
        device_id=payload.device_id,
        ip_address=payload.ip_address,
        otp_required=True,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)

    code = _generate_otp_code()
    otp = models.OTP(
        transaction_id=txn.id,
        user_id=current_user.id,
        code=code,
        expires_at=datetime.utcnow() + timedelta(seconds=OTP_TTL_SECONDS),
        max_attempts=OTP_MAX_ATTEMPTS,
    )
    db.add(otp)
    db.commit()

    log_action(
        db, current_user, "TRANSACTION_INITIATED", "transaction", txn.id,
        f"Initiated transfer of {txn.amount} {txn.currency} to {txn.receiver_account}; OTP sent."
    )

    # NOTE: In a real system the OTP would be sent via SMS/email, never returned
    # in the API response. It is returned here ONLY because this is a simulated
    # platform with no real messaging integration.
    return schemas.OTPRequestOut(
        message="OTP generated. Enter the code to verify this transaction.",
        transaction_id=txn.id,
        expires_in_seconds=OTP_TTL_SECONDS,
        debug_otp=code,
    )


@router.post("/{transaction_id}/resend-otp", response_model=schemas.OTPRequestOut)
def resend_otp(
    transaction_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    txn = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not txn or txn.sender_id != current_user.id:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if txn.status != models.TransactionStatus.PENDING_OTP:
        raise HTTPException(status_code=400, detail="This transaction is no longer awaiting OTP verification")

    code = _generate_otp_code()
    otp = models.OTP(
        transaction_id=txn.id,
        user_id=current_user.id,
        code=code,
        expires_at=datetime.utcnow() + timedelta(seconds=OTP_TTL_SECONDS),
        max_attempts=OTP_MAX_ATTEMPTS,
    )
    db.add(otp)
    db.commit()

    log_action(db, current_user, "OTP_RESENT", "transaction", txn.id, "A new OTP was generated.")

    return schemas.OTPRequestOut(
        message="A new OTP has been generated.",
        transaction_id=txn.id,
        expires_in_seconds=OTP_TTL_SECONDS,
        debug_otp=code,
    )


@router.post("/verify-otp", response_model=schemas.TransactionOut)
def verify_otp(
    payload: schemas.OTPVerify,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    txn = db.query(models.Transaction).filter(models.Transaction.id == payload.transaction_id).first()
    if not txn or txn.sender_id != current_user.id:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if txn.status != models.TransactionStatus.PENDING_OTP:
        raise HTTPException(status_code=400, detail="This transaction is not awaiting OTP verification")

    otp = (
        db.query(models.OTP)
        .filter(models.OTP.transaction_id == txn.id, models.OTP.verified == False)  # noqa: E712
        .order_by(models.OTP.created_at.desc())
        .first()
    )
    if not otp:
        raise HTTPException(status_code=400, detail="No active OTP for this transaction. Please resend.")

    if datetime.utcnow() > otp.expires_at:
        raise HTTPException(status_code=400, detail="OTP has expired. Please resend a new code.")

    if otp.attempts >= otp.max_attempts:
        txn.status = models.TransactionStatus.FAILED
        db.commit()
        raise HTTPException(status_code=400, detail="Maximum OTP attempts exceeded. Transaction cancelled.")

    if otp.code != payload.code:
        otp.attempts += 1
        current_user.failed_otp_streak += 1
        db.commit()

        activity = models.SuspiciousActivity(
            transaction_id=txn.id,
            user_id=current_user.id,
            rule_triggered="OTP_MISMATCH",
            description=f"Incorrect OTP entered (attempt {otp.attempts}/{otp.max_attempts}).",
            severity=models.Severity.LOW if otp.attempts < otp.max_attempts else models.Severity.HIGH,
        )
        db.add(activity)

        if current_user.failed_otp_streak >= USER_OTP_LOCK_STREAK:
            current_user.is_blocked = True
            db.add(models.SuspiciousActivity(
                transaction_id=txn.id,
                user_id=current_user.id,
                rule_triggered="OTP_BRUTE_FORCE",
                description=f"{current_user.failed_otp_streak} consecutive OTP failures across transactions. Account auto-blocked.",
                severity=models.Severity.CRITICAL,
            ))
            log_action(db, None, "USER_AUTO_BLOCKED", "user", current_user.id,
                       "Blocked automatically after repeated OTP failures.")

        db.commit()

        remaining = otp.max_attempts - otp.attempts
        if otp.attempts >= otp.max_attempts:
            txn.status = models.TransactionStatus.FAILED
            db.commit()
            raise HTTPException(status_code=400, detail="Incorrect OTP. Maximum attempts exceeded; transaction cancelled.")
        raise HTTPException(status_code=400, detail=f"Incorrect OTP. {remaining} attempt(s) remaining.")

    # ----- OTP correct: mark verified, reset streak, run fraud engine -----
    otp.verified = True
    current_user.failed_otp_streak = 0
    txn.status = models.TransactionStatus.PROCESSING
    db.commit()

    score, triggered = evaluate_transaction(db, current_user, txn)
    final_status = status_from_score(score)

    txn.risk_score = score
    txn.flag_reasons = "; ".join(f"[{r.code}] {r.description}" for r in triggered) if triggered else ""
    txn.status = final_status

    for r in triggered:
        db.add(models.SuspiciousActivity(
            transaction_id=txn.id,
            user_id=current_user.id,
            rule_triggered=r.code,
            description=r.description,
            severity=r.severity,
        ))

    # Register device as known if the transaction is allowed through.
    if final_status in (models.TransactionStatus.COMPLETED, models.TransactionStatus.FLAGGED) and txn.device_id:
        known = db.query(models.KnownDevice).filter(
            models.KnownDevice.user_id == current_user.id,
            models.KnownDevice.device_id == txn.device_id,
        ).first()
        if not known:
            db.add(models.KnownDevice(user_id=current_user.id, device_id=txn.device_id))

    # Deduct balance only when the funds actually move (completed or flagged-but-allowed).
    if final_status in (models.TransactionStatus.COMPLETED, models.TransactionStatus.FLAGGED):
        current_user.balance -= txn.amount

    db.commit()
    db.refresh(txn)

    log_action(
        db, current_user, f"TRANSACTION_{final_status.value.upper()}", "transaction", txn.id,
        f"Risk score {score}. Reasons: {txn.flag_reasons or 'none'}"
    )

    return txn


@router.get("/", response_model=List[schemas.TransactionOut])
def list_my_transactions(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Transaction)
        .filter(models.Transaction.sender_id == current_user.id)
        .order_by(models.Transaction.created_at.desc())
        .all()
    )


@router.get("/{transaction_id}", response_model=schemas.TransactionOut)
def get_transaction(
    transaction_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    txn = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if txn.sender_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to view this transaction")
    return txn
