from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class AdminUser(Base):
    __tablename__ = "ADMIN_USER"

    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String(100), unique=True, nullable=False)
    email         = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role          = Column(String(20), default="admin", nullable=False)  # admin / superadmin
    is_active     = Column(Boolean, default=True, nullable=False)
    last_login    = Column(DateTime(timezone=True), nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
