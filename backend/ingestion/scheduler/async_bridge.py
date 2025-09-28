"""Async wrapper to run blocking scraper in a thread."""
import asyncio
from backend.ingestion.instagram_ingestion.instagram_scraper import scrape_account

async def async_scrape(username: str, max_downloads: int):
    return await asyncio.to_thread(scrape_account, username, True, max_downloads)
