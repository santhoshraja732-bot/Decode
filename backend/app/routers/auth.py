from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import hash_password, verify_password, create_access_token
from ..audit import log_action

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserRegister, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=models.UserRole.USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_action(db, user, "USER_REGISTERED", "user", user.id, f"New account created for {user.username}")

    token = create_access_token({"sub": user.id, "role": user.role.value})
    return schemas.Token(access_token=token, user=schemas.UserOut.model_validate(user))


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="This account has been blocked. Contact support.")

    log_action(db, user, "USER_LOGIN", "user", user.id, f"{user.username} logged in")

    token = create_access_token({"sub": user.id, "role": user.role.value})
    return schemas.Token(access_token=token, user=schemas.UserOut.model_validate(user))
