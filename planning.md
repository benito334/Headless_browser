# CIRS Agent – Project Planning (Fresh Start)

## 📌 Goal

Build an AI chatbot that ingests transcripts, medical journals, EPUBs, and video/audio content, then organizes snippets into structured **learning modules** (objectives, lectures, quizzes, references). It must:


## 1) High-level approach
Ingest media → (Instagram scraper module for video/audio) → transcribe and normalize locally (GPU) → extract / annotate metadata → chunk & embed locally (GPU) → store in vector DB + content store → query online LLMs (selectable) with RAG → pedagogy generator layers that turn clusters of content into teachable modules and reference resources → deliver through a polished web UI.

---

## 2) Key principles
- **Local-first, GPU-accelerated**: RTX 2070 Super handles transcription, diarization, embeddings.
- **Provenance**: Every snippet carries citations + timestamps.
- **Retrieval > fine-tune** (RAG pipeline before model fine-tuning).
- **Protected modules**: The imported **Instagram scraper** from `Headless_browser` is preserved. Integration happens around it.
- **Modular LLM access**: Select GPT, Gemini, Claude, etc. in UI.
- **UI-first workflow**: All functionality exposed via API + React frontend.
- **Human-in-the-loop review** for medical content.
- **Local storage priority:** all raw files, transcripts, and embeddings live on a mapped local drive.
- **Containerized components:** use Docker Compose to separate ingestion, transcription, vector DB, and API/UI into individual services for faster builds and modular scaling.
- **Scalable architecture**: modular, versioned, metadata-rich.
---

## 3) Ingestion Components

### Instagram (Working)
- Uses imported Headless_browser repo for login + scraping.
- **Protected**: Do not rewrite internals.
- Wrapped with async bridge (`asyncio.to_thread`).
- Saves video/audio + metadata.

### YouTube
- Ingest via yt-dlp (audio only).
- Store audio + metadata.

### PDFs / ePubs
- Parse with Grobid / pdfminer / ebooklib.
- Extract text + metadata.

### Journals / Structured Data
- Metadata (PubMed, DOI, authors, year).
- Text + references.

---

## 4) Metadata schema

| Field          | Type        | Notes                                |
| -------------- | ----------- | ------------------------------------ |
| source_id      | UUID (TEXT) | Unique ID per record                 |
| source_type    | TEXT        | instagram / youtube / journal / epub |
| original_url   | TEXT        | Original media URL                   |
| file_path      | TEXT        | Local path to stored file            |
| publish_date   | DATETIME    | Publish date from source             |
| author         | TEXT        | Username (Instagram) or channel name |
| length_seconds | INTEGER     | Media length in seconds              |
| language       | TEXT        | Language code if available           |
| license        | TEXT        | Copyright/license info               |
| ingest_date    | DATETIME    | When ingested                        |
| notes          | TEXT        | Free-form notes                      |

---
**Containerization:**

* `ingestion` container: Playwright + yt-dlp.
* `transcription` container (future): WhisperX + pyannote + GPU libs.
* `vectordb` container: Qdrant/Weaviate.
* `api_ui` container: FastAPI + React.
  All share a mapped local volume (`/data`).

## 5) Milestones (Incremental Build)

### Milestone 1 – Instagram Core Integration
- [x] Import working Instagram scraper → `backend/ingestion/instagram_ingestion/`.
- [ ] Add async wrapper for scheduler.
- [ ] Store downloads + metadata in SQLite.
- [ ] Simple FastAPI endpoint to trigger ingestion.
- [ ] Log results to UI.

### Milestone 2 – Scheduler & Settings
- [ ] Scheduler runs ingestion jobs (interval, cutoff date).
- [ ] UI: configure accounts, frequency, max downloads/session.
- [ ] API: `/start`, `/stop`, `/check_now`.

### Milestone 3 – YouTube Ingestion
- [ ] Add YouTube URL ingestion (audio download only).
- [ ] Store metadata + transcripts.
- [ ] Add ability to paste YouTube URL into UI.
- [ ] Use yt-dlp to download video audio.
- [ ] Save files to local storage with metadata (URL, date, title).
- [ ] Implement duplicate checks and error handling.

### Milestone 4 – PDF/ePub Ingestion
- [ ] Build text parsing + metadata pipeline.
- [ ] Store full text + per-section metadata
- [ ] Implement Grobid, PyMuPDF, and ebooklib for parsing.
- [ ] Extract text, chapters, and bibliographic metadata.
- [ ] Store raw + parsed text locally with source tracking.
- [ ] Insert metadata into DB (DOI, authors, year, journal, section).

### Milestone 5 – Transcription & Processing
- [ ] GPU-based WhisperX for transcription.
- [ ] pyannote.audio for diarization.
- [ ] Embed with BGE-large/SBERT.
- [ ] Store vectors in Qdrant/Weaviate.
- [ ] Write script to pass audio → WhisperX → JSON transcript with timestamps.
- [ ] Add **pyannote.audio** for speaker diarization.
- [ ] Implement post-ASR cleaning: punctuation, abbreviation expansion, spellcheck.
- [ ] Store raw + cleaned transcripts separately.

## **Milestone 6 – Metadata & Storage**

5.1 Set up SQLite (PoC) → Postgres (later).
5.2 Define schema: source_id, type, URL, path, timestamps, authors, confidence, etc.
5.3 Write script to insert transcript + metadata into DB.
5.4 Store raw files in `/content` on local drive.

### **Milestone 7 – Embeddings & Vector DB**

6.1 Install SentenceTransformers or BGE model with GPU.
6.2 Implement semantic chunking (200–600 words, preserve context).
6.3 Embed chunks + store vectors in Qdrant (Docker).
6.4 Test query → retrieve top-k chunks.

### **Milestone 8 – RAG Retrieval**

7.1 Build retrieval function (embedding search + optional BM25).
7.2 Implement reranker (lightweight transformer or heuristics).
7.3 Integrate LLM query (GPT-4 default, UI-selectable).
7.4 Return answers with inline citations (source_id:timestamp).

### **Milestone 9 – Pedagogy Generator**

8.1 Implement clustering (HDBSCAN/k-means) to group related content.
8.2 Create module generator:

* Learning objectives
* Lecture script (with citations)
* Quiz (MCQs + short answers)
* Reading list
  8.3 Add human-in-the-loop review process.

### **Milestone 10 – Web UI**

9.1 Set up FastAPI backend + React frontend skeleton.
9.2 Build **Transcript Viewer** (searchable, filterable).
9.3 Build **Q&A Mode** (RAG chatbot).
9.4 Build **Learning Mode** (modules + export to PDF/PPT/quiz).
9.5 Add **Model Selector Dropdown** (GPT-4, Gemini, Claude).

### **Milestone 11 – QA & Scalability**

10.1 Track ASR WER and retrieval precision/recall.
10.2 Add monitoring/logging (Prometheus/Grafana).
10.3 Implement sharded vector DB scaling.
10.4 Add metadata-rich filters (peer-reviewed vs. social, date range).
10.5 Version control for transcripts/modules.

---

## 6) Folder Structure

project-root/
│
├── backend/
│ ├── ingestion/
│ │ ├── instagram_ingestion/ # Headless_browser code lives here
│ │ ├── youtube_ingestion/
│ │ ├── pdf_ingestion/
│ │ └── epub_ingestion/
│ │
│ ├── api/
│ ├── db/
│ └── config.py
│
├── frontend/
│ ├── src/
│ └── public/
│
├── data/ # local storage for downloaded files
├── logs/
├── docker-compose.yml
└── planning.md


**Notes:**

* All services share the local `./data` and `./db` volumes so they can access audio files and metadata.
* `transcription` service is configured with NVIDIA runtime for GPU workloads.
* `vectordb` runs as its own container (Qdrant by default).
* `api_ui` serves both FastAPI and React UI (can be split later).
