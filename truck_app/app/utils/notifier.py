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
