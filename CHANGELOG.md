# Changelog

All notable changes to this project will be documented in this file.

## [v6.0.0] - Smart Pick & UI Update (i18n & UX Overhaul)

### ✨ Internationalization & UI Overhaul
- **Full i18n Support:** Added comprehensive Multi-Language support (EN/TR) to the Chrome Extension with dynamic toggling and localized tooltips.
- **Icon & Branding Update:** Refreshed desktop shortcut and UI icons for a seamless neon aesthetic. Overrode aggressive Windows icon caches.
- **Syntax & Bug Squashing:** Completely resolved the string interpolation and quote escaping issues (`tier_mega_viral` syntax error) that froze the extension UI.

### 🔮 Smart Suggestion Engine (Prophet's Pick Evolved)
- **Smart Pick Popup:** "Prophet's Pick" has been upgraded to a non-intrusive "Smart Pick" toast/popup with dynamically translated CTA buttons (Clone, Debate, DNA).
- **Clickable Cards:** Made the entire Smart Pick card area clickable, opening the YouTube video in a new background tab without interfering with the action buttons.

## [v2.0.0] - Enterprise Architecture & 1-Click Install

### 🏗️ Refactored (The Great Refactor)
- **Modular Service Layer:** Surgically decomposed the monolithic `server.pyw` (4,100+ lines) into clean, standalone modules under the `app/` package, adhering to SOLID principles and single-responsibility guidelines.
- **`app/database/db.py`:** Centralized async SQLite engine using Write-Ahead Logging (WAL) and automatic migration management.
- **`app/services/security.py`:** Encapsulated AES-128 Fernet encryption for API keys and PBKDF2 cryptography for secure user sessions.
- **`app/services/email_service.py`:** Extracted dynamic multilingual report and verification code email distribution logic.
- **`app/services/ai_service.py`:** Decoupled external API orchestrations for Groq (Llama-3.3-70B) and Google Gemini 2.0 Flash models.
- **`app/services/competitor.py`:** Modularized yt-dlp integrated competitor research and dynamic metrics computing algorithms.
- **`app/services/analysis_engine.py`:** Separated the core multimedia engines combining OpenCV, librosa audio tracking, and DeepFace vision models.

### 🚀 Added
- **`install.bat` (1-Click Installer):** Formulated an advanced Windows setup script that handles Python diagnostics, establishes an isolated `venv`, installs dependencies from `requirements.txt`, automatically downloads and configures FFmpeg binaries, and spawns a desktop launching shortcut.

---

## [v1.2.0] - Security & Quality Update

### 🔒 Security
- **CryptoManager (Fernet Encryption):** All sensitive data (Groq API key, Gemini API key, SMTP password) is now encrypted with AES-128 via `cryptography.fernet` before being stored in the database. The encryption key is stored in `.secret.key` and is excluded from Git via `.gitignore`.
- **Backward Compatibility:** Old unencrypted values are seamlessly read as-is via a fallback mechanism, so existing users won't lose their settings on upgrade.

### 🛠️ Fixed
- **Async Coroutine Bug (`generate_dynamic_feedback`):** `generate_dynamic_feedback` was a synchronous function calling an `async` function (`generate_ai_game_feedback`) without `await`, returning a raw coroutine object instead of a string. This caused a crash when attempting to concatenate the result. Fixed by making `generate_dynamic_feedback` `async` and adding `await` at both the call inside it and all 4 call sites in `analyze_video`.
- **Fail Fast — No More Fake Data (`analyze_video_tech`):** When a video had no audio channel or was corrupt, the system silently returned a fake `tech_score: 5.0` report. This has been replaced with a proper `raise ValueError(...)` that immediately surfaces a clear, honest error message to the user.

### 📦 Dependencies
- Added `cryptography>=42.0.0` to `requirements.txt`.

---

## [v1.1.0] - Open Source & SaaS Standards Update

### 🔥 Added
- **Global FFmpeg Requirement Warning:** Added a critical warning in `README.md` to ensure external users are aware of the FFmpeg dependency.
- **FFmpeg Installation Guide:** Linked a manual installation video and terminal script (`winget`) for users to easily setup FFmpeg.

### 🛠️ Fixed
- **Dynamic Path Resolution:** Replaced all hardcoded personal computer paths (e.g., `C:\Users\...\`) with dynamic, environment-agnostic relative paths using `%~dp0`, `$PSScriptRoot`, and `os.path`.
- **Shortcut & Deploy Scripts:** Fixed `MASAUSTU_KISAYOL_OLUSTUR.ps1` and `deploy.bat` to work properly on any user's machine regardless of where the repository is cloned.
- **Cross-Platform Compatibility:** Ensured Python scripts (`search_app.py`) dynamically resolve static files, preventing file-not-found errors for external contributors.
