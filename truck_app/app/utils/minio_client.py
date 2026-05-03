from minio import Minio
from app.config import settings
import uuid, io

client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False
)

def ensure_bucket_exists():
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)

def upload_id_proof(file_data: bytes, filename: str, content_type: str) -> str:
    ensure_bucket_exists()
    unique_filename = f"kyc/{uuid.uuid4()}_{filename}"
    client.put_object(
        bucket_name=settings.MINIO_BUCKET,
        object_name=unique_filename,
        data=io.BytesIO(file_data),
        length=len(file_data),
        content_type=content_type
    )
    return unique_filename