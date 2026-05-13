from app.config import settings

MSG_TEMPLATES = {
    "Verified": "Dear {name}, your {kyc_type} KYC on GoGoTruk has been verified. You can now make bookings.",
    "Rejected": "Dear {name}, your {kyc_type} KYC on GoGoTruk has been rejected. Reason: {reason}. Please re-submit with correct documents.",
}


def notify_kyc_status_change(name: str, mobile: str, email: str, kyc_type: str, status: str, reason: str = ""):
    message = MSG_TEMPLATES[status].format(name=name, kyc_type=kyc_type, reason=reason or "Not specified")

    if settings.DEV_MODE:
        print(f"\n[NOTIFICATION] KYC {status} — {kyc_type}")
        print(f"  Name:    {name}")
        print(f"  Mobile:  {mobile}")
        print(f"  Email:   {email}")
        print(f"  Message: {message}\n")
        return

    _send_sms(mobile, message)
    _send_email(email, name, status, kyc_type, message)


def notify_document_expiry(owner, vehicle, doc_name: str, days_left: int):
    if days_left < 0:
        subject = f"EXPIRED: {doc_name} for vehicle {vehicle.registration_number}"
        message = (
            f"Dear {owner.first_name}, your {doc_name} for vehicle "
            f"{vehicle.registration_number} has expired. "
            f"The vehicle has been marked inactive until documents are renewed."
        )
    else:
        subject = f"Expiry Alert: {doc_name} expires in {days_left} days"
        message = (
            f"Dear {owner.first_name}, your {doc_name} for vehicle "
            f"{vehicle.registration_number} expires in {days_left} days. "
            f"Please renew it to avoid service disruption."
        )

    if settings.DEV_MODE:
        print(f"\n[NOTIFICATION] {subject}")
        print(f"  Owner:   {owner.first_name} {owner.last_name}")
        print(f"  Mobile:  {owner.mobile}")
        print(f"  Email:   {owner.email}")
        print(f"  Message: {message}\n")
        return

    _send_sms(owner.mobile, message)
    _send_email(owner.email, owner.first_name, subject, "", message)


def notify_booking_reviewed(customer, booking):
    if booking.status == "Confirmed":
        message = (
            f"Dear {customer.first_name}, your booking (ID: {booking.id}) for {booking.booking_date} "
            f"has been CONFIRMED by the truck owner. Pickup: {booking.pickup_address}."
        )
        subject = "Booking Confirmed — GoGoTruk"
    else:
        message = (
            f"Dear {customer.first_name}, your booking (ID: {booking.id}) for {booking.booking_date} "
            f"has been REJECTED. Reason: {booking.rejection_reason or 'Not specified'}."
        )
        subject = "Booking Rejected — GoGoTruk"

    if settings.DEV_MODE:
        print(f"\n[NOTIFICATION] {subject}")
        print(f"  Customer: {customer.first_name} {customer.last_name}")
        print(f"  Mobile:   {customer.mobile}")
        print(f"  Email:    {customer.email}")
        print(f"  Message:  {message}\n")
        return

    _send_sms(customer.mobile, message)
    _send_email(customer.email, customer.first_name, subject, "", message)


def notify_booking_auto_rejected(customer, booking):
    message = (
        f"Dear {customer.first_name}, your booking (ID: {booking.id}) for {booking.booking_date} "
        f"was auto-rejected as the truck owner did not respond within 2 hours. Please try another truck."
    )
    subject = "Booking Auto-Rejected — GoGoTruk"

    if settings.DEV_MODE:
        print(f"\n[NOTIFICATION] {subject}")
        print(f"  Customer: {customer.first_name} {customer.last_name}")
        print(f"  Mobile:   {customer.mobile}")
        print(f"  Message:  {message}\n")
        return

    _send_sms(customer.mobile, message)
    _send_email(customer.email, customer.first_name, subject, "", message)


def notify_cancellation(customer, owner, booking, log):
    charge_msg = f"Cancellation charge: ₹{log.cancellation_charge_amount:,.2f} ({log.cancellation_charge_pct}%). Refund: ₹{log.refund_amount:,.2f}."

    customer_msg = (
        f"Dear {customer.first_name}, your booking (ID: {booking.id}) for {booking.booking_date} "
        f"has been cancelled by {log.cancelled_by}. {charge_msg}"
    )
    owner_msg = (
        f"Dear {owner.first_name}, booking (ID: {booking.id}) for {booking.booking_date} "
        f"has been cancelled by {log.cancelled_by}. Reason: {log.reason}. "
        f"The truck slot has been released."
    )

    if settings.DEV_MODE:
        print(f"\n[NOTIFICATION] Booking Cancelled — ID: {booking.id}")
        print(f"  Cancelled by: {log.cancelled_by}")
        print(f"  Reason:       {log.reason}")
        print(f"  Charge:       {log.cancellation_charge_pct}% = ₹{log.cancellation_charge_amount:,.2f}")
        print(f"  Refund:       ₹{log.refund_amount:,.2f} ({log.refund_status})")
        print(f"  Customer SMS: {customer_msg}")
        print(f"  Owner SMS:    {owner_msg}\n")
        return

    _send_sms(customer.mobile, customer_msg)
    _send_sms(owner.mobile, owner_msg)
    _send_email(customer.email, customer.first_name, "Booking Cancelled — GoGoTruk", "", customer_msg)


def notify_invoice_sent(customer, invoice):
    message = (
        f"Dear {customer.first_name}, your invoice {invoice.invoice_number} "
        f"for ₹{invoice.total_amount:,.2f} has been generated. "
        f"Download it from the GoGoTruk app."
    )
    subject = f"Invoice {invoice.invoice_number} — GoGoTruk"

    if settings.DEV_MODE:
        print(f"\n[NOTIFICATION] {subject}")
        print(f"  Customer: {customer.first_name} {customer.last_name}")
        print(f"  Email:    {customer.email}")
        print(f"  Amount:   ₹{invoice.total_amount:,.2f}")
        print(f"  PDF URL:  {invoice.invoice_pdf_url}\n")
        return

    _send_email(customer.email, customer.first_name, subject, "", message)


def notify_booking_created(owner, booking):
    message = (
        f"Dear {owner.first_name}, a new booking request has been submitted for your truck "
        f"(Fleet ID: {booking.fleet_id}) on {booking.booking_date}. "
        f"Goods: {booking.goods_type}, {booking.goods_weight_kg} kg. "
        f"Pickup: {booking.pickup_address}. Please review and confirm on GoGoTruk."
    )

    if settings.DEV_MODE:
        print(f"\n[NOTIFICATION] New Booking Request — Booking ID: {booking.id}")
        print(f"  Owner:   {owner.first_name} {owner.last_name}")
        print(f"  Mobile:  {owner.mobile}")
        print(f"  Email:   {owner.email}")
        print(f"  Message: {message}\n")
        return

    _send_sms(owner.mobile, message)
    _send_email(owner.email, owner.first_name, "New Booking Request on GoGoTruk", "", message)
    _send_fcm_push(owner, "New Booking Request", f"Review booking for {booking.booking_date}")


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
