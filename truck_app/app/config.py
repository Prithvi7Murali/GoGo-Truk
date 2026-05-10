from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    SECRET_KEY: str
    SUPABASE_URL: str
    SUPABASE_KEY: str
    DEV_MODE: bool = True  # set False in production to enforce real OTP delivery
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = ""
    MSG91_API_KEY: str = ""
    MSG91_SENDER_ID: str = "GOTRUK"

    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()