import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/attendance_db")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-jwt-key-change-me")
    SECRET_HMAC_KEY = os.getenv("SECRET_HMAC_KEY", "your-hmac-secret-key-change-me")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "your-email@gmail.com")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your-app-password")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@college.edu")

settings = Settings()
