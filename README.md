# 🎬 YouTube Analyzer Pro (SaaS Edition) 🚀

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)](https://tensorflow.org)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-8E75C2?style=for-the-badge&logo=google-gemini&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![1-Click Install](https://img.shields.io/badge/1--Click_Install-✅_Windows-brightgreen?style=for-the-badge&logo=windows&logoColor=white)](#-1-click-kurulum-sadece-bir-tikla)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Auto_Install-007808?style=for-the-badge&logo=ffmpeg&logoColor=white)](#-1-click-kurulum-sadece-bir-tikla)

YouTube Analyzer Pro (SaaS Edition) is a **production-grade**, AI-powered analysis and optimization platform designed for content creators to maximize their video performance, SEO infrastructure, and visual content.

Built entirely on an **asynchronous database architecture**, **hardware-based GPU acceleration**, and **advanced computer vision** technologies, this system aims to transform amateur content creators into professional channels.

---

## 🆕 What's New in v2.0.0 — "Enterprise Architecture & 1-Click Install"

This major milestone upgrades the application to a high-performance, modular enterprise architecture and introduces an automated, hassle-free environment setup.

### 🏗️ 1. Enterprise Architecture & Service-Layer Decomposition (The Great Refactor)
- **Monolithic code is gone:** Surgically refactored the massive 4,100+ lines `server.pyw` module, cleanly separating the business logic and database interactions into dedicated packages while maintaining 100% backward compatibility and zero API endpoint breakage.
- **`app/database/db.py` (Database Layer):** Centralized SQLite WAL-mode async initialization, sessions, and migration pipelines.
- **`app/services/security.py` (Security Service):** Encapsulated all cryptography routines, password hashing, and token operations.
- **`app/services/email_service.py` (Notification Service):** Modularized SMTP configuration and automated localized PDF report email delivery.
- **`app/services/ai_service.py` (AI Orchestrator):** Decoupled Groq (Llama 3.3 70B) and Gemini 2.0 Flash integrations.
- **`app/services/competitor.py` (Competitor Intelligence):** Extracted specialized competitive analysis and keyword extraction logic.
- **`app/services/analysis_engine.py` (Analysis Core):** Decoupled sound, video frame rate, and DeepFace/OpenCV analysis engines.

### 🚀 2. Automated 1-Click Setup (`install.bat`)
- Designed an enterprise-grade Windows batch installer that automates pre-requisite checks, virtual environment isolation (`venv`), Python dependency setups, FFmpeg automated binaries extraction, and creates a desktop launch shortcut.

> 📜 **Full Version History:** See the [CHANGELOG.md](./CHANGELOG.md) for detailed release notes of past versions.

---

## ✨ Advanced Highlighted Features

### 🤖 1. AI Coach & Smart Recommendation Engine
*   **Groq (Llama-3.3-70B) Integration:** Synthesizes channel-specific target audiences, categories, and performance scores to offer personalized, constructive, and directly actionable feedback.
*   **Anti-Generic Rule System:** The AI never gives cliché advice like *"Be engaging in the first 10 seconds"*. Instead, it provides concrete scenarios and timestamp-coded editing examples on **"how"** to improve (*e.g., Application Example: At 00:02, add the text 'Secret Revealed!' on the screen along with a shake effect.*).
*   **Intelligence Protection:** Algorithmically respects correctly entered tags and never flags them as "irrelevant," protecting the channel's hard work.

### 👁️ 2. Computer Vision & Thumbnail Intelligence
*   **Gemini 2.0 Flash Vision Integration:** Analyzes your thumbnail designs through the eyes of artificial intelligence.
*   **Emotion & Contrast Analysis:** Evaluates facial expressions (using `deepface`), color palettes (using `colorthief`), contrast, text readability, and overall visual appeal to boost Click-Through Rate (CTR).
*   **Video Flow & Pace Analysis:** Detects in-video scenes, frame transitions, and pacing peaks to map out exactly where viewers might get bored.

### 🎙️ 3. Multimedia Audio & Pace Analysis Module
*   **Librosa & Soundfile Integration:** Analyzes audio waves within video files.
*   **Excitement & Pace Coefficient:** Identifies speech rate, volume peaks, and waves of excitement to map out a pacing graph. This optimizes audience retention throughout the video.

### 📈 4. Asynchronous & High-Performance Infrastructure
*   **aiosqlite & WAL Mode:** The SQLite database operates fully asynchronously with `Write-Ahead Logging (WAL)` mode enabled. This prevents UI or server freezes/lockups even when hundreds of analyses are run concurrently.
*   **Performance Autopilot:** Automatically detects CPU cores, RAM size, and CUDA cores at startup to deploy optimal multi-threading and hardware acceleration.
*   **GPU Hardware Acceleration:** The FFmpeg engine scans for NVIDIA (`h264_nvenc`), AMD (`h264_amf`), and Intel (`h264_qsv`) graphics cards to handle video processing at lightning speeds using GPU power.

### 🌐 5. Global SaaS Standards
*   **Multi-language Infrastructure (TR / EN / ES):** Excel-based dynamic localization (`translations.xlsx`) enables changing the entire interface, PDF reports, and AI analysis language to Turkish, English, or Spanish with a single click.
*   **Advanced PDF Report Engine:** Generates professional, elegant, industry-standard reports using the `ReportLab` library. Features flawless custom fonts and character support (`arial.ttf` safe loading).
*   **SMTP Mail Dispatcher:** Sends analysis results and PDF reports directly to the user's email address with a stylish template in just one click.
*   **SaaS Security Layer:** Highest-level protection for user accounts and data via PBKDF2 hashing and secure session token management.

---

## 🔒 Zero Knowledge & Privacy-First Policy

The biggest advantage of this application is that **your data and API keys are completely secure:**
1.  **Local Storage (Local DB):** All your analyses, history logs, and API keys are encrypted and stored locally in your computer's `channels.db` SQLite database rather than a remote SaaS server.
2.  **Open Source Security:** Your API keys are never shared with external servers; they are only transmitted directly to the official Google Gemini and Groq API endpoints via secure HTTPS.
3.  Supported by `.gitignore` rules, your database, API keys, or local log files will never be accidentally uploaded to public GitHub repositories.

---

## ⚡ 1-Click Kurulum (Sadece Bir Tıkla!)

> [!IMPORTANT]
> **Yeni! Tek tıkla kurulum artık mevcut.** Python dışında hiçbir şey kurmanıza gerek yok — FFmpeg, sanal ortam ve masaüstü kısayolu **otomatik** olarak ayarlanır.

### 🪟 Windows — En Kolay Yol

1. **Python 3.10+** yüklü olduğundan emin olun → [python.org/downloads](https://www.python.org/downloads/)  
   *(Kurulumda **"Add Python to PATH"** kutucuğunu işaretlemeyi unutmayın!)*
2. Repoyu klonlayın veya ZIP olarak indirin.
3. Proje klasöründe **`install.bat`** dosyasına **çift tıklayın**.

Script otomatik olarak şunları yapar:

| Adım | İşlem | Açıklama |
|------|-------|----------|
| 1 | 🐍 Python kontrolü | Sürüm ve PATH doğrulaması |
| 2 | 📦 venv + pip | İzole sanal ortam + tüm paketler |
| 3 | 🎬 FFmpeg | Varsa kullanır, yoksa otomatik indirir |
| 4 | 🖥️ Kısayol | Masaüstüne tek tıkla başlatıcı atar |

Kurulum tamamlandığında masaüstünüzde **"YouTube Analiz Pro"** kısayolu hazır olacak.

---

## 📋 Requirements

> [!NOTE]
> **`install.bat` kullanıyorsanız bu adımları atlayabilirsiniz** — script her şeyi otomatik halleder.

Manuel kurulum yapmak isteyenler için:

*   **Python 3.10 or higher:** [Download Python](https://www.python.org/downloads/) (Make sure to check *"Add Python to PATH"* during installation!)
*   **FFmpeg (For Video Analysis):** Automatically installed by `install.bat`. For manual install:
    *   *Easy:* `winget install Gyan.FFmpeg` (PowerShell as Admin)
    *   *Manual:* [How to Install FFmpeg on Windows](https://www.youtube.com/watch?v=JR36oH35Fgg)

---

## 🚀 Installation & Launch Options

### Option A — ⚡ 1-Click Install (RECOMMENDED)

```
Double-click  →  install.bat
```

That's it. The installer handles Python packages, FFmpeg, and creates a desktop shortcut automatically.

### Option B — Manual Setup

#### 1. Clone or Download the Repository
```bash
git clone https://github.com/oguzemirtopuz/YouTube-Analiz-Uygulamasi-Saas-Edition.git
cd YouTube-Analiz-Uygulamasi-Saas-Edition
```

#### 2. Create a Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

#### 3. Launch the Application
After installation, **3 different launching options** are available:

*   **Option A (1-Click Shortcut):** Use the desktop shortcut created by `install.bat` — launches instantly.
*   **Option B (BAT):** Double-click `BASLAT.bat` or `launch.bat` in the folder.
*   **Option C (PowerShell):** Run `Start-YouTubeAnalyzer.ps1` for the most stable silent launch.

> 💡 **Shortcut Wizard:** Double-click `KISAYOL_OLUSTUR.bat` to create additional desktop shortcuts.

### Accessing the Interface
When the application starts, a sleek, modern **PyWebView desktop window** will open. Browser access:
*   **Address:** [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🛠️ First Configuration & User Guide

1.  **Create a User Account:** Upon entering the interface, create your encrypted local account and log in.
2.  **Enter Your API Keys:** Enter your **Groq API Key** and **Google Gemini API Key** (which you can get for free) in the Settings panel. These keys are saved securely in your local SQLite database.
3.  **Define a Channel:** Add your channel type (e.g., Gaming, Education, Vlog) and target audience in the *"Add Channel"* section.
4.  **Start Analyzing:** Upload your video to the system (or enter the YouTube link/metadata details). The AI Coach will generate your complete report in seconds and can email it to you with a single click!

---

## 🔄 How to Update & Backup Guide

### ⚠️ What Data to Back Up First
Before upgrading your application to a new version, always back up the following critical files to avoid losing your configurations, history, or custom translations:
1. **`channels.db`**: This is your local SQLite database located in the application directory. It contains all your local user accounts, channel configurations, historical analyses, and encrypted API keys.
2. **`translations.xlsx`**: If you have customized any interface translations, dynamic texts, or PDF labels, keep a copy of this Excel file.

### 🚀 Step-by-Step Update Process

#### Method A: If Installed via Git (Recommended)
1. **Back up your database:** Copy `channels.db` and `translations.xlsx` to a safe location outside the project folder.
2. **Fetch and apply the latest changes:**
   ```bash
   git stash
   git pull origin main
   git stash pop
   ```
3. **Restore your database:** Copy your backed-up `channels.db` and `translations.xlsx` files back into the project folder (overwriting the default ones if necessary).
4. **Update Python dependencies:**
   ```bash
   pip install -r requirements.txt --upgrade
   ```
5. **Run the application:** Launch it using your preferred method (PowerShell, BAT, or VBS).

#### Method B: If Downloaded as a ZIP
1. **Save your database:** Copy `channels.db` and `translations.xlsx` to a safe location outside the project directory.
2. **Download and Extract:** Download the latest release ZIP from GitHub and extract it.
3. **Merge/Replace Files:** Copy all the newly extracted files over your existing installation.
4. **Restore Database:** Move your saved `channels.db` and `translations.xlsx` back into the main directory.
5. **Update Dependencies:**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

---

## 👤 About the Developer

This project was developed by **Oğuz Emir Topuz**.

*   **Age:** 14
*   **Interests & Passions:** Football enthusiast and an advanced software developer.
*   **Work & Focus:** Building SaaS applications, modern and elegant websites, and 3D games.
*   **Contact & Portfolio:** [My GitHub Profile](https://github.com/oguzemirtopuz)

---

⭐ If you liked this project, don't forget to give it a star! It will continue to be developed with new SaaS features.
