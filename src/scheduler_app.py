import signal
import sys
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from loguru import logger

from src.config import TARGET_ACCOUNT, SCRAPE_INTERVAL, LOG_LEVEL, MAX_NEW_VIDEOS_PER_RUN, DOWNLOAD_DIR
from src.db import init_db, get_connection, get_seen_post_ids, save_new_posts
from src.instagram_scraper import scrape_account

logger.remove()
logger.add(sys.stderr, level=LOG_LEVEL)
logger.add("/data/scraper.log", rotation="10 MB", level=LOG_LEVEL, enqueue=True)


def scrape_job():
    logger.info("Running scrape job at {}", datetime.utcnow().isoformat())
    posts = scrape_account(TARGET_ACCOUNT, download=True, max_downloads=MAX_NEW_VIDEOS_PER_RUN)
    if not posts:
        logger.warning("No posts scraped for {}", TARGET_ACCOUNT)
        return

    conn = get_connection()
    existing_ids = set(get_seen_post_ids(conn))

    new_posts = [p for p in posts if p["id"] not in existing_ids and p["media_type"] == "video"][:MAX_NEW_VIDEOS_PER_RUN]
    if new_posts:
        save_new_posts(conn, new_posts)
        for p in new_posts:
            logger.info("New video found: {url}", **p)
    else:
        logger.info("No new videos found or limit reached (max {}).", MAX_NEW_VIDEOS_PER_RUN)


def main():
    init_db()
    scheduler = BlockingScheduler()
    scheduler.add_job(scrape_job, "interval", minutes=SCRAPE_INTERVAL, next_run_time=datetime.utcnow())

    def shutdown(signum, frame):
        logger.info("Shutdown signal received. Exiting scheduler.")
        scheduler.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    logger.info("Starting scheduler for account {} every {} minutes. Download dir: {}", TARGET_ACCOUNT, SCRAPE_INTERVAL, DOWNLOAD_DIR)
    scheduler.start()


if __name__ == "__main__":
    main()
