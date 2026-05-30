# Changelog

All notable changes to **YouTube Analyse Pro SaaS Edition** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

### 👑 v5.5.0 — Elite Calibration Update
- **[Algorithm] Synergy & DR Protection:** Switched DNA scoring to a weighted model (40/40/10/10) with a +20 Synergy Bonus for high Hook/Tempo and a 50-credit minimum DR protection against weak CTAs.
- **[UI/UX] Dynamic DNA Badges:** Introduced 4 new gradient-styled badge tiers (Legendary, Viral Potential, Strong, Needs Improvement) based on the calculated DNA score.
- **[UI/UX] Info Guide Revamp:** Completely redesigned the Chrome Extension's Info panel with detailed explanations of the DNA scoring methodology, tier systems, and UI button mappings.
- **[Feature] Metadata Fallback:** Added a robust fallback mechanism that analyzes Video Title, Tags, and Description if the transcript is missing, dynamically flagging the UI with an "Estimated Analysis" amber warning.
- **[Prompt Engineering] Master Prompt Generator:** DNA results now automatically construct an advanced LLM script-writing prompt based on the exact anatomical triggers of the analyzed video.

---

### 🔮 v4.5.1 — Prophet's Pick Hotfix
- **[Prophet's Pick] AI Validation Filter:** Added a concurrent Groq AI validation layer for the top 10 highest-velocity videos to filter out generic/irrelevant trending videos before rendering.
- **[UI/UX] Clickable Cards:** Made the entire Prophet's Pick card area clickable, opening YouTube in a new background tab without interfering with Clone/Debate action buttons.
- **[Prompt Engineering] Strict Niche Enforcement:** Updated the AI prompt generating search queries to explicitly ban generic terms and enforce content-specific targeting.

---

### 🔮 v4.5.0 — Prophet's Pick Edition
- **[Prophet's Pick] Dynamic AI Queries:** Generates search queries via Groq tailored to the user's registered `content_type` and `purpose`.
- **[UI/UX] Matrix Glow Cards:** Injects a dynamic 3-card grid with neon Matrix glow when the user is not on a video tab.
- **[Educational UX] Context-Aware Info Modal:** The `ℹ️` button now teaches users whether they are in "Discovery", "Strategy", or "Intelligence" mode.
- **[Self-Filtering] Dynamic Channel Blacklist:** Automatically prevents the user's own videos from appearing in AI-generated trending suggestions.

---

### 🧠 v4.4.0 — Prophet Edition (Predictive Intelligence)
- **[AI] 5-Tier Spectrum:** 🔴 DEAD → 🔵 MEGA VIRAL analysis with dynamic AI persona.
- **[Algorithm] Velocity & Penetration:** View velocity and subscriber penetration ratio metrics.
- **[Features] Matrix Vision & Debate AI:** Neon outlier radar + multi-agent debate (Critic vs. Wizard vs. Referee).
- **[NLP] Chaos Metric:** 100% local algorithm to measure competitor rage and tempo.
- **[Fixes] Zero-Hallucination Armor:** Fixed "Happy Face" hallucination and Turkish/English 'B' suffix parsing bug.

---

### 🎯 v4.3.0 — The Precision Update
- **[Rabbit Hole] Dynamic Compatibility:** SQLite-integrated dynamic context fetching for niche compatibility.
- **[Extension] Robust JSON Parser:** Strips markdown and renders UI cards securely.
- **[Analytics] Chaos Metric UI:** Added human-readable explanation for the 10-point mathematical calculation.

---

### 🌪️ v4.2.0 — The Chaos & Debate Update
- **[AI Debate] A/B Test Simulator:** AI Persona debate engine with Referee evaluation.
- **[DB] SQLite WAL Mode:** Write-Ahead Logging for concurrent read performance.
- **[Crypto] Fail-Fast:** CryptoManager throws HTTP 500 on corrupted keys.
- **[Scraping] yt-dlp Backoff:** Exponential backoff against HTTP 429 bans.

---

### 🔒 v4.1.0 — Security & Logic Hardening
- **[Security] Google OAuth XSS Shield:** Serialized OAuth callbacks with `json.dumps`.
- **[Logic] Groq API Decryption Fix:** Added `CryptoManager.decrypt` to all AI endpoints.
- **[Math] Shorts Scoring Fix:** Realigned Shorts scoring weights to sum correctly to `1.00`.
- **[Stability] Transcript NameError Shield:** Pre-initialized `last_api_error` to prevent NameErrors.

---

### 🌟 v4.0.0 — SaaS Edition
- **SaaS Architecture:** Multi-user support, authentication, and secure localized credential storage.
- **Advanced Computer Vision:** Multi-threaded scene transition mapping and OpenCV threshold computing.

---

*(Earlier version histories can be found within the repository commit history.)*
