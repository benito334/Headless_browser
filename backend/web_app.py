from flask import Flask, render_template, request, redirect, url_for, flash
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger
import os, json
from pathlib import Path

from backend.config import (
    TARGET_ACCOUNT as DEFAULT_ACCOUNT,
    SCRAPE_INTERVAL as DEFAULT_INTERVAL,
    MAX_NEW_VIDEOS_PER_RUN as DEFAULT_MAX_DOWNLOADS,
    DOWNLOAD_DIR as DEFAULT_DOWNLOAD_DIR,
)
from backend.ingestion.instagram_ingestion.instagram_scraper import scrape_account
from backend.db.db import init_db, get_connection, get_seen_post_ids, save_new_posts

SETTINGS_PATH = Path(DEFAULT_DOWNLOAD_DIR) / "settings.json"

BASE_DIR = Path(__file__).resolve().parent.parent
app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))
app.secret_key = os.getenv("FLASK_SECRET", "changeme")

scheduler = BackgroundScheduler()
# do not start scheduler automatically


def load_settings():
    if SETTINGS_PATH.exists():
        return json.loads(SETTINGS_PATH.read_text())
    return {
        "target_account": DEFAULT_ACCOUNT,
        "interval": DEFAULT_INTERVAL,
        "max_downloads": DEFAULT_MAX_DOWNLOADS,
        "download_dir": DEFAULT_DOWNLOAD_DIR,
    }


def save_settings(data):
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(data))


def scheduled_job():
    settings = load_settings()
    logger.info("Job: scraping {}", settings["target_account"])
    posts = scrape_account(
        settings["target_account"],
        download=True,
        max_downloads=settings["max_downloads"],
    )
    if not posts:
        logger.warning("No posts scraped.")
        return
    conn = get_connection()
    existing_ids = set(get_seen_post_ids(conn))
    new_posts = [
        p for p in posts if p["id"] not in existing_ids and p["media_type"] == "video"
    ]
    save_new_posts(conn, new_posts)


@app.route("/", methods=["GET", "POST"])

def settings():
    data = load_settings()
    if request.method == "POST":
        data["target_account"] = request.form["target_account"].strip()
        data["interval"] = int(request.form["interval"])
        data["max_downloads"] = int(request.form["max_downloads"])
        data["download_dir"] = request.form["download_dir"].strip()
        save_settings(data)
        flash("Settings saved", "success")
        return redirect(url_for("settings"))
    running = scheduler.running and scheduler.get_jobs()
    return render_template("settings.html", settings=data, running=running, active="settings")


@app.route("/start")

def start():
    data = load_settings()
    if scheduler.running:
        flash("Scheduler already running", "info")
    else:
        scheduler.add_job(
            scheduled_job,
            "interval",
            minutes=data["interval"],
            id="scraper_job",
        )
        scheduler.start()
        flash("Scheduler started", "success")
    return redirect(url_for("settings"))


@app.route("/logs")

def logs():
    log_file = Path(DEFAULT_DOWNLOAD_DIR) / "scraper.log"
    if log_file.exists():
        lines = log_file.read_text().splitlines()[-20:]
        content = "\n".join(lines)
    else:
        content = "No log file yet."
    return render_template("logs.html", logs=content, active="logs")


@app.route("/stop")

def stop():
    if scheduler.running:
        scheduler.remove_all_jobs()
        scheduler.shutdown(wait=False)
        flash("Scheduler stopped", "success")
    else:
        flash("Scheduler not running", "info")
    return redirect(url_for("settings"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
