from typing import List, Dict
import os
import requests
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Data directory handling
# ---------------------------------------------------------------------------
# All ingestion sources should store raw files inside a shared data folder that
# can be mounted from the host. We derive the base directory from the DATA_DIR
# environment variable (default "./data") and create the instagram subfolder on
# import so that the rest of the scraper logic can assume the directory exists.
# ---------------------------------------------------------------------------
BASE_DATA_DIR = os.getenv("DATA_DIR", "./data")
INSTAGRAM_DIR = os.path.join(BASE_DATA_DIR, "instagram")

# Ensure directories exist at import-time so that the first download does not
# race to create them concurrently across multiple threads/processes.
Path(INSTAGRAM_DIR).mkdir(parents=True, exist_ok=True)

# For backward-compatibility with the original code we simply point the local
# DOWNLOAD_DIR variable (previously imported from config) to this new path.
DOWNLOAD_DIR = INSTAGRAM_DIR
from loguru import logger
from .metadata_utils import build_metadata, write_sidecar
from backend.ingestion.download_registry import is_downloaded, record_download
from backend.config import WAIT_MIN_SECONDS, WAIT_MAX_SECONDS
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
 
INSTAGRAM_BASE = "https://www.instagram.com"
 
 
def scrape_account(username: str, download: bool = False, max_downloads: int = 1000) -> List[Dict]:
    """Scrape the Instagram feed of a public account for posts.

    Returns list of metadata dicts.
    """
    posts: List[Dict] = []
    downloads_done = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
            locale="en-US",
        )
        page = context.new_page()
        target_url = f"{INSTAGRAM_BASE}/{username}/"
        logger.debug("Navigating to {}", target_url)
        try:
            page.goto(target_url, timeout=60000)
            # Wait for posts grid
            page.wait_for_selector("article", timeout=60000)

            # Collect anchors to posts
            anchors = page.query_selector_all("article a")
            for a in anchors:
                href = a.get_attribute("href")
                if not href:
                    continue
                if href.startswith("/"):
                    url = f"{INSTAGRAM_BASE}{href}"
                else:
                    url = href

                # Extract post id from url: /p/<shortcode>/
                try:
                    parts = [part for part in href.split("/") if part]
                    # take the last meaningful segment (shortcode)
                    post_id = parts[-1] if parts[-1] not in ("reel", "p", "tv") else parts[-2]
                except Exception:
                    continue

                # Open post to detect media type reliably
                media_type = "image"
                video_src = None
                try:
                    post_page = context.new_page()
                    post_page.goto(url, timeout=60000)
                    has_video = post_page.query_selector("video") is not None
                    if has_video:
                        media_type = "video"
                        video_el = post_page.query_selector("video")
                        video_src = video_el.get_attribute("src") if video_el else None
                        if not video_src:
                            meta = post_page.query_selector("meta[property='og:video']")
                            if meta:
                                video_src = meta.get_attribute("content")
                        # get upload timestamp
                        upload_ts = None
                        ts_meta = post_page.query_selector("meta[property='og:video:upload_date']")
                        if ts_meta:
                            try:
                                upload_ts = int(ts_meta.get_attribute("content"))
                            except (TypeError, ValueError):
                                pass
                    logger.debug("Post {} classified as {}", post_id, media_type)
                    post_page.close()
                except Exception as e:
                    logger.exception("Failed to inspect post {}: {}", url, e)

                # Date posted placeholder (could be extracted later)
                date_str = ""
                if media_type == "video" and upload_ts:
                    from datetime import datetime
                    date_str = datetime.utcfromtimestamp(upload_ts).strftime("%Y%m%dT%H%M%S")
                post_meta = {
                    "id": post_id,
                    "url": url,
                    "date_posted": date_str,
                    "media_type": media_type,
                }

                if media_type == "video" and video_src and downloads_done < max_downloads:
                    if is_downloaded(post_id):
                        logger.debug("Post {} already recorded; skipping download", post_id)
                        continue

                    if not download:
                        logger.debug("download=False, not fetching video but will log metadata")
                        dest_path = Path(DOWNLOAD_DIR) / f"{post_id}.mp4"
                    
                    try:
                        Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
                        ts_suffix = post_meta["date_posted"] or str(int(time.time()))
                        dest_path = Path(DOWNLOAD_DIR) / f"{post_id}_{ts_suffix}.mp4"
                        if not dest_path.exists():
                            logger.debug("Downloading video {}", video_src)
                            r = requests.get(video_src, timeout=120)
                            with open(dest_path, "wb") as f:
                                f.write(r.content)
                            downloads_done += 1
                            logger.info("Downloaded video to {} ({} / {})", dest_path, downloads_done, max_downloads)
                        else:
                            logger.debug("Video {} already exists on disk", dest_path)

                        # Write metadata sidecar regardless of download skip_ffprobe etc.
                        meta = build_metadata(
                            original_url=url,
                            file_path=str(dest_path),
                            author=username,
                            publish_date=date_str,
                            notes="scraped via pipeline"
                        )
                        write_sidecar(meta)
                        record_download(post_id, source_type="instagram", original_url=url, file_path=str(dest_path))

                        # polite delay
                        import random, time as _time
                        delay = random.uniform(WAIT_MIN_SECONDS, WAIT_MAX_SECONDS)
                        logger.debug("Sleeping %.1f seconds to avoid rate-limits", delay)
                        _time.sleep(delay)
                    except Exception as e:
                        logger.exception("Failed to download video {}: {}", url, e)

                posts.append(post_meta)
        except PlaywrightTimeoutError:
            logger.error("Timeout while loading Instagram page for {}", username)
        except Exception as e:
            logger.exception("Error scraping Instagram: {}", e)
        finally:
            context.close()
            browser.close()

    logger.info("Scraped {} posts from {} ({} videos downloaded)", len(posts), username, downloads_done)
    return posts
