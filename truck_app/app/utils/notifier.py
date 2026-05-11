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
