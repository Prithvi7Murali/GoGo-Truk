from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db

try:
    import jwt as pyjwt
    _JWT_AVAILABLE = True
except ImportError:
    _JWT_AVAILABLE = False

try:
    import bcrypt as _bcrypt
    _BCRYPT_AVAILABLE = True
except ImportError:
    _BCRYPT_AVAILABLE = False


def hash_password(password: str) -> str:
    if not _BCRYPT_AVAILABLE:
        raise RuntimeError("bcrypt not installed — run: pip install bcrypt")
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    if not _BCRYPT_AVAILABLE:
        raise RuntimeError("bcrypt not installed")
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(admin_id: int, username: str, role: str) -> str:
    if not _JWT_AVAILABLE:
        raise RuntimeError("PyJWT not installed — run: pip install PyJWT")
    payload = {
        "sub":      str(admin_id),
        "username": username,
        "role":     role,
        "exp":      datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return pyjwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict:
    if not _JWT_AVAILABLE:
        raise RuntimeError("PyJWT not installed")
    return pyjwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])


def get_current_admin(authorization: str = Header(...), db: Session = Depends(get_db)):
    from app.models.admin_user import AdminUser
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError
        payload = decode_token(token)
        admin = db.query(AdminUser).filter(AdminUser.id == int(payload["sub"]), AdminUser.is_active == True).first()
        if not admin:
            raise ValueError
        return admin
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_superadmin(admin=Depends(get_current_admin)):
    if admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Superadmin access required")
    return admin
