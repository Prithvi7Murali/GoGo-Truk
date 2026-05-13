from app.celery_app import celery_app


def _send_booking_notification(booking_id: int):
    from app.database import SessionLocal
    from app.models.booking import Booking
    from app.models.fleet import Fleet
    from app.models.kyc import OwnerKYC
    from app.utils.notifier import notify_booking_created

    db = SessionLocal()
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return
        fleet = db.query(Fleet).filter(Fleet.id == booking.fleet_id).first()
        owner = db.query(OwnerKYC).filter(OwnerKYC.id == fleet.owner_kyc_id).first()
        notify_booking_created(owner, booking)
    finally:
        db.close()


def _auto_reject_booking(booking_id: int):
    from datetime import datetime, timezone
    from app.database import SessionLocal
    from app.models.booking import Booking
    from app.models.availability import Availability, AvailabilityStatus
    from app.models.kyc import CustomerKYC
    from app.utils.notifier import notify_booking_auto_rejected

    db = SessionLocal()
    try:
        booking = (
            db.query(Booking)
            .filter(Booking.id == booking_id)
            .with_for_update()
            .first()
        )
        if not booking or booking.status != "Pending":
            return

        booking.status = "Rejected"
        booking.rejection_reason = "Auto-rejected: owner did not respond within 2 hours"

        slot = db.query(Availability).filter(Availability.id == booking.availability_id).first()
        if slot:
            slot.status = AvailabilityStatus.AVAILABLE

        db.commit()

        customer = db.query(CustomerKYC).filter(CustomerKYC.id == booking.customer_kyc_id).first()
        if customer:
            notify_booking_auto_rejected(customer, booking)

        from app.utils.cache import cache_delete_pattern
        cache_delete_pattern("search:*")
    finally:
        db.close()


if celery_app:
    @celery_app.task(name="send_booking_notification")
    def send_booking_notification(booking_id: int):
        _send_booking_notification(booking_id)

    @celery_app.task(name="auto_reject_booking")
    def auto_reject_booking(booking_id: int):
        _auto_reject_booking(booking_id)
