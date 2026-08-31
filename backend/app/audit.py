from typing import Optional
from sqlalchemy.orm import Session

from . import models


def log_action(
    db: Session,
    actor: Optional[models.User],
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[str] = None,
):
    entry = models.AuditLog(
        actor_id=actor.id if actor else None,
        actor_username=actor.username if actor else "system",
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
    db.add(entry)
    db.commit()
    return entry
