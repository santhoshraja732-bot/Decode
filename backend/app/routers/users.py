from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=schemas.UserOut)
def read_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.get("/directory", response_model=List[schemas.DirectoryEntry])
def list_directory(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Registered accounts a user can send money to (excludes admins and self),
    so the sender doesn't need to already know someone's account number."""
    users = (
        db.query(models.User)
        .filter(
            models.User.role == models.UserRole.USER,
            models.User.id != current_user.id,
            models.User.is_blocked == False,  # noqa: E712
        )
        .order_by(models.User.username)
        .all()
    )
    return [
        schemas.DirectoryEntry(account_number=u.account_number, username=u.username)
        for u in users
    ]
