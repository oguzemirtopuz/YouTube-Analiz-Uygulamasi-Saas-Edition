<div align="center">
  <h1>🚀 YT Analiz Pro - The Ultimate YouTube Hacking Ecosystem</h1>
  <p><strong>A full-stack SaaS platform combining an AI-powered Desktop App with a Viral Cloning Chrome Extension.</strong></p>
</div>

---

✨ **Latest Release (v4.1.0)**
> [!IMPORTANT]
> **Code Quality & Security Hardening — Groq Decryption & Google OAuth XSS Shield**
> 
> * **[Security] Google OAuth XSS Shield:** Patched a cross-site scripting (XSS) vulnerability in the Google OAuth callback endpoint. Previously, user session details were injected directly into a single-quoted JavaScript string when saving to `localStorage`. This could allow arbitrary script execution if a username contained single quotes or malicious payloads. All session objects are now serialized as double-quoted JSON strings using `json.dumps()` before injection.
> * **[Logic] Groq API Decryption Fix:** Resolved a critical issue in the AI Chat and analysis endpoints where stored Groq API keys were retrieved from the SQLite database and sent to the API raw (encrypted). This prevented AI-driven analysis and chat from functioning. Incorporated `CryptoManager.decrypt` to properly decrypt keys at runtime.
> * **[Math] Corrected Shorts Scoring Scale:** Fixed the scoring weights used in YouTube Shorts overall score calculations. Previously, the weights (`retention=0.45`, `tech=0.35`, `seo=0.10`) summed to `0.90`, capping the maximum possible score at `9.0` instead of `10.0`. Restructured weights to `retention=0.50`, `tech=0.35`, and `seo=0.15` to form a perfect `1.00` sum (maximum 10.0 score).
> * **[PDF] Cleaned Multiple Headers in Report PDF:** Fixed a layout bug in the PDF exporter where the "SEO & Thumbnail Balance Warning" header was duplicated in the document flow due to copy-paste errors.
> * **[Async] Non-blocking Email Status:** Simplified the email notification logic inside `analyze_video` to prevent false positives (where `email_sent` was marked `True` even if the delivery failed). Sending status is now accurately determined based on active SMTP credentials.
> * **[Performance] Discarded Heavy Test Imports:** Removed `from starlette.testclient import TestClient` from the production `api_send_report` endpoint, reducing runtime memory overhead and startup latency.
> * **[Stability] Prevented NameError in Subtitle Engine:** Initialized `last_api_error` before the `try-except` block in `_fetch_transcript_sync` to avoid `NameError` exceptions when subtitle fetching fails.
> * **[CV] Non-Pro Visual Tempo Resolution:** Fixed a visual tempo map rendering bug where non-pro analyses were generating empty maps. Reduced the non-pro frame skip threshold from the video's FPS to 1 frame to ensure a rich density map.
> * **[Competitor] Robust Channel & Title Check:** Enhanced competitor filtering by cross-referencing multiple attributes (channel name, uploader name, and channel ID) to reliably exclude the user's own channel from competitor metrics. Added a new `check_content_consistency` helper to check title/tag/description keyword overlap.

### 📜 Changelog
#### 🔒 v4.1.0 — Security & Logic Hardening
- **[Security] Google OAuth XSS Shield:** Serialized OAuth callbacks with `json.dumps` to prevent potential JavaScript injection.
- **[Logic] Groq API Decryption Fix:** Added `CryptoManager.decrypt` to ensure Groq API keys are decrypted before calling AI endpoints.
- **[Math] Shorts Puanlama Düzeltmesi:** Realigned Shorts scoring weights (`0.50` / `0.35` / `0.15`) to sum to `1.00`.
- **[PDF] Cleaned Multiple Headers:** Removed duplicated warning headers in the exported PDF layout.
- **[Async] E-Posta Gönderim Mantığı:** Standardized `email_sent` dynamically based on SMTP check.
- **[Performance] Test Client Import Removed:** Cleaned unused test framework import from production API.
- **[Stability] Transcript NameError Shield:** Pre-initialized `last_api_error` in altyazı motoru to prevent NameErrors on failure.
- **[CV] Visual Tempo Map:** Changed threshold frame count for non-pro analysis to generate tempo data correctly.
- **[Competitor] Own Channel Exclusion & Keyword Sync:** Upgraded competitor check using robust ID/Name matching and added a content consistency utility.

#### 🌟 v4.0.0 — YouTube Analiz Pro SaaS Edition
- **SaaS Architecture:** Introduced multi-user support, authentication, and secure localized credential storage.
- **Advanced Computer Vision:** Multi-threaded scene transition mapping and OpenCV threshold computing.

---

YT Analiz Pro is not just an analytics tool; it is a **YouTube Growth Ecosystem** designed to dissect videos mathematically, clone viral structures, and dominate competitor channels using advanced AI and computer vision.

---

## 🌟 Ecosystem Overview

The project is split into two perfectly synced engines:

### 1. The Core (Desktop Application)
A heavy-duty backend built with **Python, FastAPI, and PyQt5**, powered by OpenCV and Librosa for deep, frame-by-frame video analysis.
* **Computer Vision Analysis:** Detects scene cuts, fast-paced edits, and brightness variations using OpenCV.
* **Audio & Silence Detection:** Uses Librosa to analyze audio tempo, dead air (silences), and decibel peaks.
* **Retention Scoring Algorithm:** Calculates a highly accurate "Retention Score" based on hook momentum, frame density, and pacing.
* **AI Coach (Groq & Gemini):** Analyzes thumbnails, reads video transcripts, and provides actionable, brutal feedback to improve content retention.
* **Database & Security:** AES-encrypted API key storage (Groq/Gemini) with SQLite for tracking past analyses.

### 2. The Weapon (Chrome Extension)
A sleek, neon-themed **Chrome Extension** that injects directly into the YouTube interface and syncs with the Desktop App.
* **Viral Cloning Engine:** With one click (`Clone This Video`), the extension extracts a viral video's transcript, structure, and psychological triggers, generating 3 unique content hooks tailored to your own niche.
* **Channel Battles (Competitor Analysis):** Visit any competitor's channel page and click `Analyze Channel`. The extension bypasses YouTube's pagination, instantly pulls their real view counts using a hybrid `yt-dlp` engine, and pits their stats against your channel's Quality Score. The AI generates aggressive, guerrilla marketing tactics to steal their audience.
* **Rabbit Hole (Niche Finder):** Stuck on what to film next? Search a broad keyword (e.g., "Crypto"), and the Rabbit Hole module will deep-dive into YouTube to find hidden "Outlier" videos with abnormally high View Velocities.

---

## 🛠️ Tech Stack
* **Backend:** Python 3.11, FastAPI, Uvicorn, yt-dlp, SQLite, Cryptography
* **Frontend (Desktop):** PyQt5, QWebEngineView (Chart.js integration)
* **Frontend (Extension):** HTML5, Vanilla CSS (Glassmorphism), JavaScript (Manifest V3)
* **AI Integration:** Groq API (Llama-3.3-70b-versatile), Google Gemini 2.0 Flash (Vision)
* **Audio/Video Processing:** OpenCV, Librosa, FFmpeg

---

## 🚀 Installation & Quick Start

### 1-Click Desktop Installer
We made setup completely frictionless. 
1. Run `install.bat` on Windows.
2. It will automatically install Python (if missing), create a virtual environment, install all dependencies (including FFmpeg via yt-dlp), and launch the server.
3. Open the desktop app via `run.bat`!

### Chrome Extension Setup
1. Open Google Chrome and navigate to `chrome://extensions/`.
2. Enable **Developer mode** in the top right corner.
3. Click **Load unpacked** and select the `chrome_extension` folder in this repository.
4. Pin the 🚀 icon to your browser toolbar. *Make sure the Desktop App (FastAPI server) is running in the background so the extension can communicate with it.*

---

## 🛡️ License
This project is licensed under the MIT License. See the `LICENSE` file for details.
