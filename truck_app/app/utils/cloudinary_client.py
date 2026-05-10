import cloudinary
import cloudinary.uploader
import cloudinary.utils
from app.config import settings
import uuid
import re
import time
import ssl
import urllib3

# Fix for corporate VDI SSL issue
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)


def upload_document(file_data: bytes, folder: str) -> str:
    """Upload images (JPG, PNG) — publicly accessible"""
    result = cloudinary.uploader.upload(
        file_data,
        folder=folder,
        public_id=str(uuid.uuid4()),
        resource_type="image",
        access_control=[{"access_type": "anonymous"}],
    )
    return result["secure_url"]


def upload_pdf_doc(file_data: bytes, folder: str) -> str:
    """Upload PDFs — publicly accessible, correct Content-Type"""
    result = cloudinary.uploader.upload(
        file_data,
        folder=folder,
        public_id=f"{uuid.uuid4()}.pdf",
        resource_type="raw",
        access_control=[{"access_type": "anonymous"}],
    )
    return result["secure_url"]


def upload_id_proof(file_data: bytes, filename: str, content_type: str) -> str:
    if content_type == "application/pdf":
        return upload_pdf_doc(file_data, "gogotruk/kyc")
    return upload_document(file_data, "gogotruk/kyc")


def _parse_cloudinary_url(url: str) -> tuple[str, str, str]:
    """Return (public_id, resource_type, format) parsed from a Cloudinary secure_url."""
    if "/image/upload/" in url:
        resource_type = "image"
        after = url.split("/image/upload/")[1]
    elif "/raw/upload/" in url:
        resource_type = "raw"
        after = url.split("/raw/upload/")[1]
    elif "/video/upload/" in url:
        resource_type = "video"
        after = url.split("/video/upload/")[1]
    else:
        raise ValueError(f"Unrecognised Cloudinary URL: {url}")

    # Strip optional version segment (v1234567890/)
    after = re.sub(r"^v\d+/", "", after)

    if resource_type in ("image", "video"):
        parts = after.rsplit(".", 1)
        public_id = parts[0]
        fmt = parts[1] if len(parts) > 1 else ""
    else:
        # raw — public_id includes the extension
        public_id = after
        fmt = ""

    return public_id, resource_type, fmt


def get_signed_url(cloudinary_url: str, expires_in: int = 3600) -> str:
    """Return a time-limited signed download URL for any Cloudinary resource."""
    public_id, resource_type, fmt = _parse_cloudinary_url(cloudinary_url)
    return cloudinary.utils.private_download_url(
        public_id,
        fmt,
        resource_type=resource_type,
        type="upload",
        expires_at=int(time.time()) + expires_in,
    )
