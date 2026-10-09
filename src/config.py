"""Application configuration module supporting .env and environment variables."""

import os
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
TEMPLATES_DIR = BASE_DIR / "templates"
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load .env file
load_dotenv(BASE_DIR / ".env")


class Settings:
    # Execution Flags
    DRY_RUN: bool = os.getenv("DRY_RUN", "true").lower() in ("true", "1", "yes")
    REQUIRE_APPROVAL: bool = os.getenv("REQUIRE_APPROVAL", "true").lower() in ("true", "1", "yes")
    CUTOFF_HOURS: float = float(os.getenv("CUTOFF_HOURS", "2.0"))

    # AI Configuration
    AI_PROVIDER: Literal["gemini", "openai", "anthropic"] = os.getenv("AI_PROVIDER", "gemini").lower() # type: ignore
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Market Data
    COINGECKO_API_KEY: str = os.getenv("COINGECKO_API_KEY", "")
    GOLD_API_KEY: str = os.getenv("GOLD_API_KEY", "")
    ALPHAVANTAGE_API_KEY: str = os.getenv("ALPHAVANTAGE_API_KEY", "")

    # Email
    EMAIL_SERVICE: Literal["gmail", "resend"] = os.getenv("EMAIL_SERVICE", "gmail").lower() # type: ignore
    GMAIL_USER: str = os.getenv("GMAIL_USER", "")
    GMAIL_APP_PASSWORD: str = os.getenv("GMAIL_APP_PASSWORD", "")
    ALERT_RECIPIENT_EMAIL: str = os.getenv("ALERT_RECIPIENT_EMAIL", os.getenv("GMAIL_USER", ""))
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")

    # Image Hosting
    IMAGE_HOSTING: Literal["cloudinary", "s3"] = os.getenv("IMAGE_HOSTING", "cloudinary").lower() # type: ignore
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")

    # Meta Graph API
    META_PAGE_ACCESS_TOKEN: str = os.getenv("META_PAGE_ACCESS_TOKEN", "")
    FACEBOOK_PAGE_ID: str = os.getenv("FACEBOOK_PAGE_ID", "")
    INSTAGRAM_ACCOUNT_ID: str = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
    META_APP_ID: str = os.getenv("META_APP_ID", "")
    META_APP_SECRET: str = os.getenv("META_APP_SECRET", "")

    # Paths
    BASE_DIR: Path = BASE_DIR
    ASSETS_DIR: Path = ASSETS_DIR
    TEMPLATES_DIR: Path = TEMPLATES_DIR
    DATA_DIR: Path = DATA_DIR
    OUTPUT_DIR: Path = OUTPUT_DIR
    HISTORY_FILE: Path = DATA_DIR / "history.json"


settings = Settings()
