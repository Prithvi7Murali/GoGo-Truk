from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class NotificationLog(Base):
    __tablename__ = "NOTIFICATION_LOG"

    id               = Column(Integer, primary_key=True, index=True)
    event_type       = Column(String(50),  nullable=False)   # kyc_verified, booking_created, etc.
    channel          = Column(String(10),  nullable=False)   # sms | email | push | console
    recipient_mobile = Column(String(15),  nullable=True)
    recipient_email  = Column(String(255), nullable=True)
    subject          = Column(String(255), nullable=True)
    message          = Column(Text,        nullable=False)
    status           = Column(String(15),  nullable=False)   # delivered | dev_logged | failed
    error_message    = Column(Text,        nullable=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
