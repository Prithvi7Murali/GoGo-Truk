import cloudinary
import cloudinary.uploader
from app.config import settings
import uuid
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

def upload_id_proof(file_data: bytes, filename: str, content_type: str) -> str:
    unique_id = str(uuid.uuid4())
    result = cloudinary.uploader.upload(
        file_data,
        folder="gogotruk/kyc",
        public_id=unique_id,
        resource_type="auto"
    )
    return result["secure_url"]