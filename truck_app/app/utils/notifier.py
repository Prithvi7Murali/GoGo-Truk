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


def _send_sms(mobile: str, message: str):
    """Production: send SMS via MSG91"""
    if not settings.MSG91_API_KEY:
        print(f"[NOTIFIER] MSG91_API_KEY not set — SMS skipped for {mobile}")
        return
    try:
        import requests
        url = "https://api.msg91.com/api/v5/flow/"
        payload = {
            "template_id": settings.MSG91_TEMPLATE_ID,
            "short_url":   "0",
            "recipients":  [{"mobiles": f"91{mobile}", "message": message}],
        }
        headers = {
            "authkey":      settings.MSG91_API_KEY,
            "content-type": "application/json",
        }
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            print(f"[NOTIFIER] SMS sent to {mobile}")
        else:
            print(f"[NOTIFIER] SMS failed for {mobile}: {response.text}")
        _log("sms_sent", "sms", message, mobile=mobile, status="delivered"
             if response.status_code == 200 else "failed",
             error=response.text if response.status_code != 200 else None)
    except Exception as e:
        print(f"[NOTIFIER] SMS error for {mobile}: {e}")
        _log("sms_error", "sms", message, mobile=mobile, status="failed", error=str(e))


def _send_email(email: str, name: str, subject: str, kyc_type: str, message: str):
    """Production: send email via SendGrid"""
    if not settings.SENDGRID_API_KEY or not settings.SENDGRID_FROM_EMAIL:
        print(f"[NOTIFIER] SendGrid not configured — email skipped for {email}")
        return
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
            <div style="background: #E87820; padding: 20px; border-radius: 8px 8px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">GoGoTruk</h1>
                <p style="color: #fff; margin: 4px 0 0;">Logistics Platform</p>
            </div>
            <div style="background: #f9f9f9; padding: 24px; border-radius: 0 0 8px 8px;">
                <p style="font-size: 16px; color: #333;">Dear {name},</p>
                <p style="font-size: 15px; color: #555; line-height: 1.6;">{message}</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;"/>
                <p style="font-size: 12px; color: #999;">
                    This is an automated message from GoGoTruk.<br/>
                    Please do not reply to this email.
                </p>
            </div>
        </div>
        """

        mail = Mail(
            from_email=settings.SENDGRID_FROM_EMAIL,
            to_emails=email,
            subject=subject,
            html_content=html_content
        )

        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(mail)

        if response.status_code in [200, 202]:
            print(f"[NOTIFIER] Email sent to {email} — {subject}")
        else:
            print(f"[NOTIFIER] Email failed for {email}: {response.status_code}")

        _log("email_sent", "email", message, email=email,
             subject=subject,
             status="delivered" if response.status_code in [200, 202] else "failed")

    except Exception as e:
        print(f"[NOTIFIER] Email error for {email}: {e}")
        _log("email_error", "email", message, email=email,
             subject=subject, status="failed", error=str(e))


def _send_fcm_push(owner, title: str, body: str):
    """Production: send push notification via Firebase FCM"""
    if not settings.FCM_SERVER_KEY:
        print(f"[NOTIFIER] FCM_SERVER_KEY not set — push skipped for {owner.mobile}")
        return
    try:
        import requests
        headers = {
            "Authorization": f"key={settings.FCM_SERVER_KEY}",
            "Content-Type":  "application/json",
        }
        payload = {
            "to":           f"/topics/owner_{owner.id}",
            "notification": {"title": title, "body": body},
            "data":         {"owner_id": str(owner.id)},
        }
        response = requests.post(
            "https://fcm.googleapis.com/fcm/send",
            json=payload,
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            print(f"[NOTIFIER] Push sent to owner {owner.id} — {title}")
        else:
            print(f"[NOTIFIER] Push failed for owner {owner.id}: {response.text}")
        _log("push_sent", "push", body, mobile=owner.mobile,
             subject=title,
             status="delivered" if response.status_code == 200 else "failed",
             error=response.text if response.status_code != 200 else None)
    except Exception as e:
        print(f"[NOTIFIER] Push error for owner {owner.id}: {e}")
        _log("push_error", "push", body, mobile=owner.mobile,
             subject=title, status="failed", error=str(e))
