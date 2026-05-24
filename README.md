<div align="center">
  <h1>🚀 YT Analiz Pro - The Ultimate YouTube Hacking Ecosystem</h1>
  <p><strong>A full-stack SaaS platform combining an AI-powered Desktop App with a Viral Cloning Chrome Extension.</strong></p>
</div>

---

✨ **Latest Release (v4.2.0)**
> [!IMPORTANT]
> **v4.2.0 - The Chaos & Debate Update 🚀**
> 
> * **[AI Debate] A/B Test Simulator:** Introduced a Multi-Agent Debate engine (`_call_groq_debate`). Persona A (The Critic) and Persona B (The Wizard) now run in parallel to argue over the best viral strategy. The AI Referee evaluates their concepts and crowns a winner, complete with a golden neon UI card! ⚔️
> * **[Analytics] BabaClutch Chaos Metric:** A custom, 100% local, pure Python NLP algorithm (`calculate_chaos_score`) that measures the "Rage Density" and "Tempo Variance" of a competitor's transcript. Zero API cost. Predicts the potential view surge based on psychological chaos. Features a brand-new red glitch-effect UI! 🌪️
> * **[DB & Crypto] Fail-Fast Architecture:** The `CryptoManager` now strictly throws an HTTP 500 error on corrupted keys rather than failing silently. Enabled SQLite WAL (Write-Ahead Logging) mode for robust concurrent performance.
> * **[Data Leak] Empty URL Patch:** Sealed a vulnerability that allowed empty or invalid URL submissions to bypass validation.
> * **[Extension] SPA Navigation Blindness:** Solved the YouTube Single Page Application (SPA) navigation bug using a 3-layered event listener architecture.
> * **[Scraping] HTTP 429 Exponential Backoff:** Added robust exponential backoff logic for `yt-dlp` to prevent aggressive rate-limiting bans.
> * **[AI Prompt] Anti-Hallucination Directives:** Injected a strict "Human Face Ban" rule (`_build_thumbnail_rule`) across all agents for Gaming channels, completely stopping AI from hallucinating fake human emotions in thumbnail prompts.

### 📜 Changelog
#### 🌪️ v4.2.0 — The Chaos & Debate Update
- **[AI Debate] A/B Test Simulator:** AI Persona debate engine with Referee evaluation.
- **[Analytics] Chaos Metric:** Pure Python NLP algorithm to calculate transcript Rage/Tempo.
- **[DB] SQLite WAL Mode:** Enabled Write-Ahead Logging.
- **[Crypto] Fail-Fast:** CryptoManager throws HTTP 500 on corrupted keys.
- **[Data Leak] URL Patch:** Blocked empty URL submissions in the extension.
- **[Extension] SPA Fix:** 3-layered event listener for YouTube SPA routing.
- **[Scraping] yt-dlp Backoff:** Exponential backoff against HTTP 429 bans.
- **[AI Prompt] Face Ban:** Strict gaming thumbnail directive to prevent human face hallucination.

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
* **A/B Test Simulator (AI Debate):** Two distinct AI Personas (The Critic vs. The Wizard) argue in real-time to find the ultimate viral hook for your next video, judged by a Master AI Referee. ⚔️
* **BabaClutch Chaos Metric:** A 100% local, custom Python NLP algorithm that calculates the "Rage Density" and "Tempo Variance" of competitor transcripts to measure their psychological chaos level. 🌪️
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
3. Open the desktop app via `BASLAT.bat`!

### Chrome Extension Setup
1. Open Google Chrome and navigate to `chrome://extensions/`.
2. Enable **Developer mode** in the top right corner.
3. Click **Load unpacked** and select the `chrome_extension` folder in this repository.
4. Pin the 🚀 icon to your browser toolbar. *Make sure the Desktop App (FastAPI server) is running in the background so the extension can communicate with it.*

---

## 🌌 Connected Projects & Sister Ecosystems
If you like **YT Analiz Pro**, make sure to check out my other advanced AI cognitive architecture:
* **[JARVIS-Cognitive-OS](https://github.com/oguzemirtopuz/JARVIS-Cognitive-OS):** An ultra-advanced Autonomous Cognitive Operating System built with a custom semantic router, hot-reloaded tool synthesis, low-energy Whisper voice pipelines, and AST-level sandbox execution environments. 🚀

---

## 🛡️ License
This project is licensed under the MIT License. See the `LICENSE` file for details.
