# backend/ingestion/logger_setup.py  (new)
import sys
from loguru import logger
import os

def init_logger():
    logger.remove()
    level = os.getenv("LOG_LEVEL", "INFO")
    logger.add(sys.stderr, level=level, enqueue=True, backtrace=True, diagnose=False)
    # Optional: file sink
    os.makedirs("logs", exist_ok=True)
    logger.add("logs/app.log", level=level, rotation="5 MB", retention="7 days", enqueue=True)

