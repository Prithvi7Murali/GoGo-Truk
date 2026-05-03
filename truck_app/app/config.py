from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str
    SECRET_KEY: str
    SUPABASE_URL: str
    SUPABASE_KEY: str

    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()