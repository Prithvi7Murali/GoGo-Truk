from app.config import settings


def _log(event_type: str, channel: str, message: str,
         mobile: str = None, email: str = None,
         subject: str = None, status: str = "delivered", error: str = None):
    try:
        from app.database import SessionLocal
        from app.models.notification_log import NotificationLog
        db = SessionLocal()
        try:
            db.add(NotificationLog(
                event_type=event_type,
                channel=channel,
                recipient_mobile=mobile,
                recipient_email=email,
                subject=subject,
                message=message,
                status=status,
                error_message=error,
            ))
            db.commit()
        finally:
            db.close()
    except Exception:
        pass  # never let logging break the main flow


MSG_TEMPLATES = {
    "Verified": "Dear {name}, your {kyc_type} KYC on GoGoTruk has been verified. You can now make bookings.",
    "Rejected": "Dear {name}, your {kyc_type} KYC on GoGoTruk has been rejected. Reason: {reason}. Please re-submit with correct documents.",
}


def notify_kyc_status_change(name: str, mobile: str, email: str, kyc_type: str, status: str, reason: str = ""):
    message = MSG_TEMPLATES[status].format(name=name, kyc_type=kyc_type, reason=reason or "Not specified")
    event   = f"kyc_{status.lower()}"

    if settings.DEV_MODE:
        print(f"\n[NOTIFICATION] KYC {status} — {kyc_type}")
        print(f"  Name:    {name}")
        print(f"  Mobile:  {mobile}")
        print(f"  Email:   {email}")
        print(f"  Message: {message}\n")
        _log(event, "console", message, mobile=mobile, email=email, status="dev_logged")
        return

    _send_sms(mobile, message)
    _log(event, "sms", message, mobile=mobile)
    _send_email(email, name, status, kyc_type, message)
    _log(event, "email", message, email=email, subject=f"KYC {status} — GoGoTruk")


def notify_document_expiry(owner, vehicle, doc_name: str, days_left: int):
    if days_left < 0:
        subject = f"EXPIRED: {doc_name} for vehicle {vehicle.registration_number}"
        event   = "document_expired"
    else:
        subject = f"Expiry Alert: {doc_name} expires in {days_left} days"
        event   = "document_expiry_alert"

    message = (
        f"Dear {owner.first_name}, your {doc_name} for vehicle "
        f"{vehicle.registration_number} "
        + (f"has expired. The vehicle has been marked inactive until documents are renewed."
           if days_left < 0 else
           f"expires in {days_left} days. Please renew it to avoid service disruption.")
    )

    if settings.DEV_MODE:
        print(f"\n[NOTIFICATION] {subject}")
        print(f"  Owner:   {owner.first_name} {owner.last_name}")
        print(f"  Mobile:  {owner.mobile}")
        print(f"  Email:   {owner.email}")
        print(f"  Message: {message}\n")
        _log(event, "console", message, mobile=owner.mobile, email=owner.email, subject=subject, status="dev_logged")
        return

    _send_sms(owner.mobile, message)
    _log(event, "sms", message, mobile=owner.mobile, subject=subject)
    _send_email(owner.email, owner.first_name, subject, "", message)
    _log(event, "email", message, email=owner.email, subject=subject)


def notify_booking_reviewed(customer, booking):
    if booking.status == "Confirmed":
        subject = "Booking Confirmed — GoGoTruk"
        event   = "booking_confirmed"
        message = (
            f"Dear {customer.first_name}, your booking (ID: {booking.id}) for {booking.booking_date} "
            f"has been CONFIRMED by the truck owner. Pickup: {booking.pickup_address}."
        )
    else:
        subject = "Booking Rejected — GoGoTruk"
        event   = "booking_rejected"
        message = (
            f"Dear {customer.first_name}, your booking (ID: {booking.id}) for {booking.booking_date} "
            f"has been REJECTED. Reason: {booking.rejection_reason or 'Not specified'}."
        )

    if settings.DEV_MODE:
        print(f"\n[NOTIFICATION] {subject}")
        print(f"  Customer: {customer.first_name} {customer.last_name}")
        print(f"  Mobile:   {customer.mobile}")
        print(f"  Email:    {customer.email}")
        print(f"  Message:  {message}\n")
        _log(event, "console", message, mobile=customer.mobile, email=customer.email, subject=subject, status="dev_logged")
        return

    _send_sms(customer.mobile, message)
    _log(event, "sms", message, mobile=customer.mobile, subject=subject)
    _send_email(customer.email, customer.first_name, subject, "", message)
    _log(event, "email", message, email=customer.email, subject=subject)


def notify_booking_auto_rejected(customer, booking):
    subject = "Booking Auto-Rejected — GoGoTruk"
    message = (
        f"Dear {customer.first_name}, your booking (ID: {booking.id}) for {booking.booking_date} "
        f"was auto-rejected as the truck owner did not respond within 2 hours. Please try another truck."
    )

    if settings.DEV_MODE:
        print(f"\n[NOTIFICATION] {subject}")
        print(f"  Customer: {customer.first_name} {customer.last_name}")
        print(f"  Mobile:   {customer.mobile}")
        print(f"  Message:  {message}\n")
        _log("booking_auto_rejected", "console", message, mobile=customer.mobile, email=customer.email, subject=subject, status="dev_logged")
        return

    _send_sms(customer.mobile, message)
    _log("booking_auto_rejected", "sms", message, mobile=customer.mobile, subject=subject)
    _send_email(customer.email, customer.first_name, subject, "", message)
    _log("booking_auto_rejected", "email", message, email=customer.email, subject=subject)


def notify_cancellation(customer, owner, booking, log):
    charge_msg   = f"Cancellation charge: ₹{log.cancellation_charge_amount:,.2f} ({log.cancellation_charge_pct}%). Refund: ₹{log.refund_amount:,.2f}."
    customer_msg = (
        f"Dear {customer.first_name}, your booking (ID: {booking.id}) for {booking.booking_date} "
        f"has been cancelled by {log.cancelled_by}. {charge_msg}"
    )
    owner_msg = (
        f"Dear {owner.first_name}, booking (ID: {booking.id}) for {booking.booking_date} "
        f"has been cancelled by {log.cancelled_by}. Reason: {log.reason}. "
        f"The truck slot has been released."
    )
    subject = "Booking Cancelled — GoGoTruk"

    if settings.DEV_MODE:
        print(f"\n[NOTIFICATION] {subject} — ID: {booking.id}")
        print(f"  Cancelled by: {log.cancelled_by}  Reason: {log.reason}")
        print(f"  Charge: {log.cancellation_charge_pct}% = ₹{log.cancellation_charge_amount:,.2f}  Refund: ₹{log.refund_amount:,.2f}")
        print(f"  Customer SMS: {customer_msg}")
        print(f"  Owner SMS:    {owner_msg}\n")
        _log("booking_cancelled", "console", customer_msg, mobile=customer.mobile, email=customer.email, subject=subject, status="dev_logged")
        _log("booking_cancelled", "console", owner_msg,    mobile=owner.mobile,    subject=subject, status="dev_logged")
        return

    _send_sms(customer.mobile, customer_msg)
    _log("booking_cancelled", "sms", customer_msg, mobile=customer.mobile, subject=subject)
    _send_sms(owner.mobile, owner_msg)
    _log("booking_cancelled", "sms", owner_msg, mobile=owner.mobile, subject=subject)
    _send_email(customer.email, customer.first_name, subject, "", customer_msg)
    _log("booking_cancelled", "email", customer_msg, email=customer.email, subject=subject)


def notify_invoice_sent(customer, invoice):
    subject = f"Invoice {invoice.invoice_number} — GoGoTruk"
    message = (
        f"Dear {customer.first_name}, your invoice {invoice.invoice_number} "
        f"for ₹{invoice.total_amount:,.2f} has been generated. "
        f"Download it from the GoGoTruk app."
    )

    if settings.DEV_MODE:
        print(f"\n[NOTIFICATION] {subject}")
        print(f"  Customer: {customer.first_name} {customer.last_name}")
        print(f"  Email:    {customer.email}")
        print(f"  Amount:   ₹{invoice.total_amount:,.2f}")
        print(f"  PDF URL:  {invoice.invoice_pdf_url}\n")
        _log("invoice_sent", "console", message, email=customer.email, subject=subject, status="dev_logged")
        return

    _send_email(customer.email, customer.first_name, subject, "", message)
    _log("invoice_sent", "email", message, email=customer.email, subject=subject)


def notify_booking_created(owner, booking):
    subject = "New Booking Request — GoGoTruk"
    message = (
        f"Dear {owner.first_name}, a new booking request has been submitted for your truck "
        f"(Fleet ID: {booking.fleet_id}) on {booking.booking_date}. "
        f"Goods: {booking.goods_type}, {booking.goods_weight_kg} kg. "
        f"Pickup: {booking.pickup_address}. Please review and confirm on GoGoTruk."
    )

    if settings.DEV_MODE:
        print(f"\n[NOTIFICATION] {subject} — Booking ID: {booking.id}")
        print(f"  Owner:   {owner.first_name} {owner.last_name}")
        print(f"  Mobile:  {owner.mobile}")
        print(f"  Email:   {owner.email}")
        print(f"  Message: {message}\n")
        _log("booking_created", "console", message, mobile=owner.mobile, email=owner.email, subject=subject, status="dev_logged")
        return

    _send_sms(owner.mobile, message)
    _log("booking_created", "sms", message, mobile=owner.mobile, subject=subject)
    _send_email(owner.email, owner.first_name, subject, "", message)
    _log("booking_created", "email", message, email=owner.email, subject=subject)
    _send_fcm_push(owner, "New Booking Request", f"Review booking for {booking.booking_date}")
    _log("booking_created", "push", f"New Booking Request — {booking.booking_date}", mobile=owner.mobile)


def _send_fcm_push(owner, title: str, body: str):
    # Production: send via FCM HTTP API using FCM_SERVER_KEY from settings
    # Requires the owner's FCM device token (stored when they log in on mobile)
    # import requests
    # requests.post("https://fcm.googleapis.com/fcm/send", ...)
    pass


def _send_sms(mobile: str, message: str):
    # Production: integrate MSG91 here
    # import requests
    # requests.post("https://api.msg91.com/api/v5/flow/", ...)
    pass


def _send_email(email: str, name: str, status: str, kyc_type: str, message: str):
    # Production: integrate SendGrid here
    # from sendgrid import SendGridAPIClient
    # from sendgrid.helpers.mail import Mail
    # sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    # sg.send(Mail(...))
    pass
