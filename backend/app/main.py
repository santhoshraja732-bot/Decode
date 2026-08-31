from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import engine, SessionLocal
from .routers import auth, users, transactions, admin
from .security import hash_password

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DecodersPay - Fraud Prevention Platform",
    description=(
        "A simulated platform for digital transactions with OTP verification, "
        "rule-based fraud detection, and administrative oversight. "
        "No real financial transactions are performed."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # relax for local dev/demo; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(transactions.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {
        "message": "DecodersPay - Fraud Prevention Platform API",
        "docs": "/docs",
    }


@app.on_event("startup")
def seed_admin():
    """Create a default admin account on first run so the platform is usable out of the box."""
    db = SessionLocal()
    try:
        existing = db.query(models.User).filter(models.User.role == models.UserRole.ADMIN).first()
        if not existing:
            admin_user = models.User(
                username="admin",
                email="admin@fraudplatform.local",
                hashed_password=hash_password("Admin@123"),
                role=models.UserRole.ADMIN,
                balance=0,
            )
            db.add(admin_user)
            db.commit()
            print("Seeded default admin -> username: admin | password: Admin@123 (please change this)")
    finally:
        db.close()


@app.on_event("startup")
def seed_demo_users():
    """Create 5 ready-to-use demo accounts, each starting with ₹50,000, so
    transfers between registered accounts can be demoed immediately."""
    db = SessionLocal()
    demo_names = ["karthik", "meena", "arun", "kavya", "surya"]
    try:
        for username in demo_names:
            existing = db.query(models.User).filter(models.User.username == username).first()
            if existing:
                continue
            demo_user = models.User(
                username=username,
                email=f"{username}@decoderspay.local",
                hashed_password=hash_password("User@123"),
                role=models.UserRole.USER,
                balance=50000.0,
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
            print(f"Seeded demo account -> username: {username} | password: User@123 | "
                  f"account number: {demo_user.account_number} | balance: 50000")
    finally:
        db.close()
