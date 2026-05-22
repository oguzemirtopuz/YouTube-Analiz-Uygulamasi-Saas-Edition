# Changelog

All notable changes to this project will be documented in this file.

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
