<div align="center">
  <h1>🚀 YT Analiz Pro - The Ultimate YouTube Hacking Ecosystem</h1>
  <p><strong>A full-stack SaaS platform combining an AI-powered Desktop App with a Viral Cloning Chrome Extension.</strong></p>
</div>

<br>

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
