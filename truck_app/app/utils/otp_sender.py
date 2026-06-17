import os
import random
import string
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Read DEV_MODE from .env
DEV_MODE = os.getenv("DEV_MODE", "true").lower() == "true"
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "")

def generate_otp() -> str:
    """Generate a random 6 digit OTP"""
    return "".join(random.choices(string.digits, k=6))

def send_otp(mobile: str, email: str, otp: str) -> dict:
    """
    DEV MODE   → just print OTP to console, return it in response
    PROD MODE  → send OTP to user email via SendGrid, hide from response
    """
    if DEV_MODE:
        # Development — print to terminal so developer can see it
        print(f">>> [DEV MODE] OTP for {mobile}: {otp}")
        return {
            "message": "OTP sent successfully (DEV MODE)",
            "dev_otp": otp  # visible in /docs response for testing
        }
    else:
        # Production — send real email via SendGrid
        if not SENDGRID_API_KEY or not SENDGRID_FROM_EMAIL:
            raise ValueError(
                "SENDGRID_API_KEY and SENDGRID_FROM_EMAIL must be set in .env for production mode"
            )

        if not email:
            raise ValueError("User email is required to send OTP in production mode")

        message = Mail(
            from_email=SENDGRID_FROM_EMAIL,
            to_emails=email,
            subject="Your GoGoTruk Verification Code",
            html_content=f"""
                <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto;">
                    <h2 style="color: #FF6B00;">GoGoTruk Verification</h2>
                    <p>Your one-time password (OTP) is:</p>
                    <h1 style="letter-spacing: 8px; color: #333;">{otp}</h1>
                    <p>This code expires in 10 minutes.</p>
                    <p>If you did not request this, please ignore this email.</p>
                    <hr/>
                    <small style="color: #999;">GoGoTruk Logistics Platform</small>
                </div>
            """
        )

        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            sg.send(message)
            print(f">>> [PROD MODE] OTP email sent to {email}")
            return {
                "message": "OTP sent successfully"
                # dev_otp is intentionally hidden in production
            }
        except Exception as e:
            print(f">>> SendGrid error: {e}")
            raise ValueError(f"Failed to send OTP email: {str(e)}")