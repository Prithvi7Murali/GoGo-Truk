from app.utils.pdf_generator import generate_consent_pdf
from app.utils.cloudinary_client import upload_pdf_doc
import urllib.request

pdf_bytes = generate_consent_pdf(
    customer_name="Test User",
    mobile="9876543210",
    email="test@example.com",
    ip_address="127.0.0.1",
    device_info="Debug",
    timestamp="2026-05-10 10:00:00 UTC",
)

url = upload_pdf_doc(pdf_bytes, "gogotruk/test")
print(f"URL: {url}")

# Check response headers
req = urllib.request.urlopen(url)
print(f"HTTP Status:   {req.status}")
print(f"Content-Type:  {req.headers.get('Content-Type')}")
print(f"Content-Length:{req.headers.get('Content-Length')}")
