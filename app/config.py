
import os

class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")  # set in Render
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "true").lower() == "true"

    # CORS
    CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "*")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    # Example: postgres://user:pass@host:5432/dbname

class ProdConfig(Config):
    DEBUG = False

class DevConfig(Config):
    DEBUG = True
