from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.admin_user import AdminUser
from app.utils.auth import hash_password, verify_password, create_token, get_current_admin, require_superadmin

router = APIRouter(prefix="/api/admin/auth", tags=["Admin Auth"])


class SetupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AdminResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    last_login: datetime | None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: AdminResponse


@router.post("/setup", response_model=AdminResponse, status_code=201)
def setup_first_admin(data: SetupRequest, db: Session = Depends(get_db)):
    """Bootstrap the first superadmin — only works when no admins exist."""
    if db.query(AdminUser).count() > 0:
        raise HTTPException(status_code=403, detail="Admin accounts already exist. Use login instead.")
    admin = AdminUser(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        role="superadmin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    admin = db.query(AdminUser).filter(AdminUser.username == data.username).first()
    if not admin or not admin.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(data.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    admin.last_login = datetime.now(timezone.utc)
    db.commit()
    token = create_token(admin.id, admin.username, admin.role)
    return {"access_token": token, "admin": admin}


@router.get("/me", response_model=AdminResponse)
def me(admin=Depends(get_current_admin)):
    return admin


@router.post("/admins", response_model=AdminResponse, status_code=201)
def create_admin(data: SetupRequest, db: Session = Depends(get_db), _=Depends(require_superadmin)):
    """Superadmin creates a new admin account."""
    if db.query(AdminUser).filter(
        (AdminUser.username == data.username) | (AdminUser.email == data.email)
    ).first():
        raise HTTPException(status_code=409, detail="Username or email already exists")
    admin = AdminUser(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        role="admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@router.get("/admins", response_model=list[AdminResponse])
def list_admins(db: Session = Depends(get_db), _=Depends(require_superadmin)):
    return db.query(AdminUser).order_by(AdminUser.id).all()


@router.delete("/admins/{admin_id}", status_code=204)
def deactivate_admin(admin_id: int, db: Session = Depends(get_db), current=Depends(require_superadmin)):
    if admin_id == current.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    target = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Admin not found")
    target.is_active = False
    db.commit()
