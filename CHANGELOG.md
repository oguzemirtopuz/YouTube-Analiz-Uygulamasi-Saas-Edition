# Changelog

All notable changes to this project will be documented in this file.

## [v1.1.0] - Open Source & SaaS Standards Update

### 🔥 Added
- **Global FFmpeg Requirement Warning:** Added a critical warning in `README.md` to ensure external users are aware of the FFmpeg dependency.
- **FFmpeg Installation Guide:** Linked a manual installation video and terminal script (`winget`) for users to easily setup FFmpeg.

### 🛠️ Fixed
- **Dynamic Path Resolution:** Replaced all hardcoded personal computer paths (e.g., `C:\Users\...\`) with dynamic, environment-agnostic relative paths using `%~dp0`, `$PSScriptRoot`, and `os.path`.
- **Shortcut & Deploy Scripts:** Fixed `MASAUSTU_KISAYOL_OLUSTUR.ps1` and `deploy.bat` to work properly on any user's machine regardless of where the repository is cloned.
- **Cross-Platform Compatibility:** Ensured Python scripts (`search_app.py`) dynamically resolve static files, preventing file-not-found errors for external contributors.
