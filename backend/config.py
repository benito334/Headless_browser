import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

TARGET_ACCOUNT: str = os.getenv("TARGET_ACCOUNT", "")
SCRAPE_INTERVAL: int = int(os.getenv("SCRAPE_INTERVAL", "30"))  # in minutes
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
MAX_NEW_VIDEOS_PER_RUN: int = int(os.getenv("MAX_NEW_VIDEOS_PER_RUN", "4"))
WAIT_MIN_SECONDS: float = float(os.getenv("WAIT_MIN_SECONDS", "5"))
WAIT_MAX_SECONDS: float = float(os.getenv("WAIT_MAX_SECONDS", "15"))
DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", "/downloads")

if not TARGET_ACCOUNT:
    raise ValueError("TARGET_ACCOUNT environment variable must be set.")
