"""
Rule-based fraud / suspicious-activity detection engine.

Each rule inspects the transaction (and the sender's recent history) and,
if triggered, contributes risk points plus a human-readable reason. The
accumulated risk score determines whether the transaction is allowed
through, flagged, held for admin review, or blocked outright.

Thresholds are intentionally simple/configurable constants so the logic
stays transparent and easy to demo/tune for the simulation.
"""
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models

# ----- Configurable thresholds -----
HIGH_VALUE_AMOUNT = 5000
CRITICAL_VALUE_AMOUNT = 20000
VELOCITY_WINDOW_MINUTES = 10
VELOCITY_MAX_TXNS = 3
FANOUT_WINDOW_MINUTES = 30
FANOUT_MAX_DISTINCT_RECEIVERS = 5
SPIKE_MULTIPLIER = 5
NEW_DEVICE_AMOUNT_THRESHOLD = 1000

# ----- Score -> status thresholds -----
SCORE_BLOCK = 80
SCORE_HOLD = 50
SCORE_FLAG = 25


class RuleResult:
    def __init__(self, points: int, code: str, description: str, severity: models.Severity):
        self.points = points
        self.code = code
        self.description = description
        self.severity = severity


def _rule_high_value(txn) -> Optional[RuleResult]:
    if txn.amount >= CRITICAL_VALUE_AMOUNT:
        return RuleResult(
            60, "CRITICAL_AMOUNT",
            f"Transaction amount {txn.amount} exceeds the critical threshold of {CRITICAL_VALUE_AMOUNT}.",
            models.Severity.CRITICAL,
        )
    if txn.amount >= HIGH_VALUE_AMOUNT:
        return RuleResult(
            25, "HIGH_AMOUNT",
            f"Transaction amount {txn.amount} exceeds the high-value threshold of {HIGH_VALUE_AMOUNT}.",
            models.Severity.HIGH,
        )
    return None


def _rule_blacklisted_receiver(db: Session, txn) -> Optional[RuleResult]:
    hit = db.query(models.BlacklistedAccount).filter(
        models.BlacklistedAccount.account_number == txn.receiver_account
    ).first()
    if hit:
        return RuleResult(
            100, "BLACKLISTED_RECEIVER",
            f"Receiver account {txn.receiver_account} is blacklisted ({hit.reason or 'no reason given'}).",
            models.Severity.CRITICAL,
        )
    return None


def _rule_velocity(db: Session, txn) -> Optional[RuleResult]:
    window_start = datetime.utcnow() - timedelta(minutes=VELOCITY_WINDOW_MINUTES)
    count = db.query(models.Transaction).filter(
        models.Transaction.sender_id == txn.sender_id,
        models.Transaction.created_at >= window_start,
        models.Transaction.id != txn.id,
    ).count()
    if count >= VELOCITY_MAX_TXNS:
        return RuleResult(
            30, "VELOCITY",
            f"{count} other transactions were initiated by this user in the last "
            f"{VELOCITY_WINDOW_MINUTES} minutes (limit {VELOCITY_MAX_TXNS}).",
            models.Severity.HIGH,
        )
    return None


def _rule_fanout(db: Session, txn) -> Optional[RuleResult]:
    window_start = datetime.utcnow() - timedelta(minutes=FANOUT_WINDOW_MINUTES)
    distinct_receivers = db.query(func.count(func.distinct(models.Transaction.receiver_account))).filter(
        models.Transaction.sender_id == txn.sender_id,
        models.Transaction.created_at >= window_start,
    ).scalar()
    if distinct_receivers and distinct_receivers >= FANOUT_MAX_DISTINCT_RECEIVERS:
        return RuleResult(
            25, "FAN_OUT",
            f"Funds sent to {distinct_receivers} distinct accounts within {FANOUT_WINDOW_MINUTES} minutes.",
            models.Severity.MEDIUM,
        )
    return None


def _rule_spike_vs_average(db: Session, txn) -> Optional[RuleResult]:
    past = db.query(models.Transaction).filter(
        models.Transaction.sender_id == txn.sender_id,
        models.Transaction.status == models.TransactionStatus.COMPLETED,
    ).order_by(models.Transaction.created_at.desc()).limit(20).all()
    if len(past) < 3:
        return None
    avg = sum(t.amount for t in past) / len(past)
    if avg > 0 and txn.amount >= avg * SPIKE_MULTIPLIER:
        return RuleResult(
            20, "AMOUNT_SPIKE",
            f"Amount {txn.amount} is {SPIKE_MULTIPLIER}x+ this user's recent average ({avg:.2f}).",
            models.Severity.MEDIUM,
        )
    return None


def _rule_new_device(db: Session, txn) -> Optional[RuleResult]:
    if txn.amount < NEW_DEVICE_AMOUNT_THRESHOLD or not txn.device_id:
        return None
    known = db.query(models.KnownDevice).filter(
        models.KnownDevice.user_id == txn.sender_id,
        models.KnownDevice.device_id == txn.device_id,
    ).first()
    if not known:
        return RuleResult(
            20, "NEW_DEVICE",
            f"Transaction of {txn.amount} initiated from a device not previously seen for this user.",
            models.Severity.MEDIUM,
        )
    return None


def _rule_self_transfer(txn, sender_account_number: str) -> Optional[RuleResult]:
    if txn.receiver_account == sender_account_number:
        return RuleResult(
            15, "SELF_TRANSFER",
            "Sender and receiver account numbers are identical.",
            models.Severity.LOW,
        )
    return None


ALL_RULES = [
    "high_value", "blacklisted_receiver", "velocity", "fanout",
    "spike_vs_average", "new_device", "self_transfer",
]


def evaluate_transaction(db: Session, sender: models.User, txn: models.Transaction) -> Tuple[int, List[RuleResult]]:
    """Run every rule against the transaction and return (total_score, triggered_results)."""
    triggered: List[RuleResult] = []

    for fn, needs_db in (
        (_rule_high_value, False),
        (_rule_blacklisted_receiver, True),
        (_rule_velocity, True),
        (_rule_fanout, True),
        (_rule_spike_vs_average, True),
        (_rule_new_device, True),
    ):
        result = fn(db, txn) if needs_db else fn(txn)
        if result:
            triggered.append(result)

    self_transfer_result = _rule_self_transfer(txn, sender.account_number)
    if self_transfer_result:
        triggered.append(self_transfer_result)

    total_score = min(100, sum(r.points for r in triggered))
    return total_score, triggered


def status_from_score(score: int) -> models.TransactionStatus:
    if score >= SCORE_BLOCK:
        return models.TransactionStatus.BLOCKED
    if score >= SCORE_HOLD:
        return models.TransactionStatus.HELD
    if score >= SCORE_FLAG:
        return models.TransactionStatus.FLAGGED
    return models.TransactionStatus.COMPLETED
