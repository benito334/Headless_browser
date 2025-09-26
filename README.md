# Instagram Video Monitor

This project periodically monitors a public Instagram account for **new video posts** and stores their metadata in a lightweight SQLite database.

---

## Features

* Headless scraping with **Playwright (Python)** inside Docker.
* Basic anti-bot evasion (custom user-agent, waits for selectors).
* Scheduler built with **APScheduler** (interval configurable via `.env`).
* Stores metadata (post ID, URL, date posted placeholder, media type) in SQLite.
* Console & file logging via **Loguru**.

---

## Quick Start

1.  Copy the environment template and edit it:

    ```bash
    cp .env.example .env
    # Edit TARGET_ACCOUNT and SCRAPE_INTERVAL as desired
    ```

2.  Build & start the stack:

    ```bash
    docker compose up --build
    ```

3.  Logs will stream to the console and `/data/scraper.log`. The local `db_data` volume contains `instagram_posts.db`.

---

## Configuration (`.env`)

| Var             | Default | Description                             |
|-----------------|---------|-----------------------------------------|
| `TARGET_ACCOUNT`| —       | Instagram username to monitor (required)|
| `SCRAPE_INTERVAL`| `30`   | Scrape interval in **minutes**          |
| `LOG_LEVEL`     | `INFO`  | Log level (`DEBUG`, `INFO`, etc.)       |
| `MAX_NEW_VIDEOS_PER_RUN` | `10` | Max videos processed per run |
| `DOWNLOAD_DIR` | `/downloads` | Where to save downloaded videos |

---

## Folder Structure

```
.
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── src
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   ├── instagram_scraper.py
│   └── scheduler_app.py
└── README.md
```

---

## Extending

* **Postgres** – replace `db.py` with SQLAlchemy/Postgres logic and mount a Postgres service in `docker-compose.yml`.
* **Enhanced scraping** – open each post to extract `date_posted` or use GraphQL queries.

PRs and issues welcome!
