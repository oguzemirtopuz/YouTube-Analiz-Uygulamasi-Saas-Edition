<div align="center">
  <h1>🚀 YT Analiz Pro - The Ultimate YouTube Hacking Ecosystem</h1>
  <p><strong>A full-stack SaaS platform combining an AI-powered Desktop App with a Viral Cloning Chrome Extension.</strong></p>
</div>

---

✨🚀 **Latest Release (v4.5.1 PROPHET'S PICK HOTFIX)**
> [!IMPORTANT]
> **v4.5.1 - Prophet's Pick Hotfix (AI Validation & Clickable Cards) 🔮**
> 
> **A. Next-Gen Analysis Engine (Predictive Intelligence):**
> * **5-Tier AI Spectrum:** The system analyzes videos across 5 distinct tiers: 🔴 DEAD, 🟡 POTENTIAL, 🚀 RISING, 🟢 VIRAL, and 🔵 MEGA VIRAL.
> * **Dynamic Persona:** The AI shifts its personality based on the tier (e.g., a ruthless autopsy for a Dead video, but a deep system analysis for a Mega Viral video).
> * **Velocity & Time Awareness:** "View Velocity" calculation added via `uploadDate` to distinguish artificial spikes in the "Fresh Window" (first 6 hours).
> * **Subscriber Penetration:** A new metric measuring the true engagement power of the channel by calculating the ratio of views to subscriber count.
> * **Comment Signals:** Added a layer that measures "Share Potential" by analyzing the sentiment of the first 10 comments.
>
> **B. "Killer" Features:**
> * **Prophet's Pick (Dynamic Auto-Suggestion):** AI generates 3 dynamic search queries tailored exactly to your channel's niche, finds the highest-velocity trending videos, and drops them directly on your dashboard.
> * **Matrix Vision:** A passive radar that outlines "Outlier" videos with a Neon Green glow and a 🔥 TREND badge on the YouTube homepage.
> * **AI Multi-Agent Debate:** The Critic and The Wizard AIs clash with the "Debate" button, while the Referee AI produces the golden winning idea.
> * **BabaClutch Chaos Metric:** A 100% local, 0% API cost NLP algorithm analyzing competitor rage and tempo.
>
> **C. Critical Bug Fixes & Security:**
> * **"Happy Face" Annihilation:** Eradicated hardcoded AI prompts preventing the AI from hallucinating non-existent faces.
> * **Regex "B" Revolution:** Resolved the data-parsing confusion between Turkish "Bin" (Thousand) and English "Billion".
> * **Dynamic Self-Filtering:** The engine now automatically fetches your channel names from the database and scrubs your own videos from all Rabbit Hole and Prophet's Pick recommendations.

### 📜 Changelog
#### 🔮 v4.5.1 — Prophet's Pick Hotfix
- **[Prophet's Pick] AI Validation Filter:** Added a concurrent Groq AI validation layer for the top 10 highest-velocity videos to actively filter out generic/irrelevant trending videos (e.g., MrBeast) before rendering them on the dashboard.
- **[UI/UX] Clickable Cards:** Made the entire Prophet's Pick card area clickable, opening the YouTube video in a new background tab without interfering with the Clone/Debate action buttons.
- **[Prompt Engineering] Strict Niche Enforcement:** Updated the AI prompt generating search queries to explicitly ban generic terms (like "comedy" or "gaming") and strictly enforce content-specific targeting.
#### 🔮 v4.5.0 — Prophet's Pick Edition
- **[Prophet's Pick] Dynamic AI Queries:** Generates search queries via Groq specifically tailored to the user's registered `content_type` and `purpose`.
- **[UI/UX] Matrix Glow Cards:** Injects a dynamic 3-card grid with a neon Matrix glow when the user is not on a video tab.
- **[Educational UX] Context-Aware Info Modal:** The `ℹ️` button now teaches users whether they are in "Discovery", "Strategy", or "Intelligence" mode based on their active YouTube tab.
- **[Self-Filtering] Dynamic Channel Blacklist:** Automatically prevents the user's own videos from appearing in AI-generated trending suggestions.
#### 🧠 v4.4.0 — Prophet Edition (Predictive Intelligence Update)
- **[AI Model] 5-Tier Spectrum:** Analyzes videos in 🔴 DEAD, 🟡 POTENTIAL, 🚀 RISING, 🟢 VIRAL, and 🔵 MEGA VIRAL categories with dynamic personas.
- **[Algorithm] Velocity & Penetration:** Calculates view velocity and subscriber penetration ratio to detect organic momentum.
- **[Features] Matrix Vision & Debate AI:** Neon green outlier radar and multi-agent AI debate (Critic vs. Wizard vs. Referee).
- **[NLP] Chaos Metric:** 100% local NLP algorithm to measure competitor rage and tempo.
- **[Fixes] Zero-Hallucination Armor:** Fixed the "Happy Face" hallucination, resolved the Turkish/English 'B' suffix parsing bug, and added robust JSON/SPA routing protections.

#### 🎯 v4.3.0 — The Precision Update
- **[Rabbit Hole] Dynamic Compatibility:** SQLite integrated dynamic context fetching for niche compatibility.
- **[Extension] Robust JSON Parser:** Strips markdown and renders UI cards securely.
- **[Analytics] Chaos Metric UI:** Added human-readable explanation for the 10-point mathematical calculation.
- **[AI Prompt] Strict Format & Creativity:** Re-tuned `_call_groq_clone` to preserve high-creativity ideas while enforcing `{...}` JSON format.

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
* **[JARVIS-Cognitive-OS (v16.1.0 ARCHITECT UPDATE)](https://github.com/oguzemirtopuz/JARVIS-Cognitive-OS)** 🤖
  * **Armored Sandbox:** AST Sandbox made 100% secure, blocking deep Python vulnerabilities like `__builtins__`, `getattr`, `__import__`.
  * **Zero Leak (Memory):** Fixed the bug where data deleted from ChromaDB remained hanging in RAM; TF-IDF matrix is now cleared asynchronously.
  * **1-Click Installation:** Added a PowerShell-based, error-handled automatic FFmpeg downloader and PATH integrator.
  * **DevOps:** Updated `requirements.txt` and `README.md`, sealed the v16.1.0 tag on GitHub.

---

## 🛡️ License
This project is licensed under the MIT License. See the `LICENSE` file for details.
