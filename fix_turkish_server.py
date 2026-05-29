# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
"""
fix_turkish_server.py
=====================
Translates all remaining Turkish comments, docstrings, print/log messages,
and user-facing API error strings in server.pyw to English.

SAFETY RULES (strictly enforced):
  - Only string literals, comments, and docstrings are touched.
  - Variable names, function names, class names, DB keys are NEVER changed.
  - Every replacement is an EXACT string match — no regex on code logic.
  - A backup copy is made before any changes.
"""

import shutil
import os

SRC = "server.pyw"
BACKUP = "server.pyw.bak_turkish"

# ---------------------------------------------------------------------------
# Build the full replacement table.
# Format: (exact_old_string, exact_new_string)
# Order matters for overlapping substrings — longer/more-specific first.
# ---------------------------------------------------------------------------
REPLACEMENTS = [

    # ── Docstrings ──────────────────────────────────────────────────────────
    (
        '    """Kullanıcı bazlı logger döndürür. logs/user_X.log dosyasına yazar."""',
        '    """Returns a per-user logger. Writes to logs/user_X.log."""',
    ),
    (
        '    """Sistem başlangıcında donanım profilini tespit eder."""',
        '    """Detects hardware profile at system startup."""',
    ),
    (
        '    """\n    Sırasıyla NVIDIA, AMD, Intel GPU codec\'lerini dener.\n    Çalışan ilkini döndürür, hiçbiri çalışmazsa libx264 (CPU) döndürür.\n    """',
        '    """\n    Tries NVIDIA, AMD, and Intel GPU codecs in order.\n    Returns the first working one; falls back to libx264 (CPU) if none work.\n    """',
    ),
    (
        '    """\n    Video süresine göre dinamik FFmpeg timeout hesaplar.\n    Kural: max(min_timeout, video_süresi * 2)\n    20GB+ dosyalar için bile yeterli marj sağlar.\n    Süre bulunamazsa None döner (timeout yok).\n    """',
        '    """\n    Calculates a dynamic FFmpeg timeout based on video duration.\n    Rule: max(min_timeout, video_duration * 2)\n    Provides sufficient margin even for 20GB+ files.\n    Returns None if duration cannot be determined (no timeout).\n    """',
    ),
    (
        '    """Yüklenen dosyaları diske kopyalar (threadpool içinde çalıştırılmak üzere)."""',
        '    """Copies uploaded files to disk (intended to run inside a threadpool)."""',
    ),
    (
        '    """422 Pydantic validation hatalarını logla ve anlamlı JSON dön."""',
        '    """Logs 422 Pydantic validation errors and returns a meaningful JSON response."""',
    ),
    (
        '    """\n    Fail-Fast (Aşama 1) Kuralı: Şifreleme çözülemediğinde sessizce boş string dönmek YASAKTIR.\n    Bu global handler, herhangi bir API endpointinde CryptoDecryptionError fırlatıldığında\n    dürüstçe 500 hatası ve anlamlı mesaj döner.\n    """',
        '    """\n    Fail-Fast (Phase 1) Rule: Silently returning an empty string when decryption fails is FORBIDDEN.\n    This global handler returns an honest 500 error with a meaningful message\n    whenever a CryptoDecryptionError is raised in any API endpoint.\n    """',
    ),
    (
        '    """Google OAuth2 yetkilendirme URL\'sini oluşturur."""',
        '    """Generates the Google OAuth2 authorization URL."""',
    ),
    (
        '    """Google OAuth2 callback — token exchange ve kullanıcı oluşturma/giriş."""',
        '    """Google OAuth2 callback — token exchange and user creation/login."""',
    ),
    (
        '    """Google OAuth Client ID ve Secret kaydet."""',
        '    """Save Google OAuth Client ID and Secret."""',
    ),
    (
        '    """Tüm beklenmeyen hataları yakalayıp kullanıcıya hata kodu gösterir."""',
        '    """Catches all unexpected errors and returns an error code to the user."""',
    ),
    (
        '    """Manuel rapor gönderimi — Sonuç ekranından \'Raporu Tekrar Gönder\' butonu."""',
        '    """Manual report dispatch — triggered by the \'Resend Report\' button on the results screen."""',
    ),
    (
        '    """content_type\'a göre thumbnail direktifi döndürür."""',
        '    """Returns a thumbnail directive based on content_type."""',
    ),
    (
        '    """\n    Groq Llama-3 ile viral klonlama konsepti üretir.\n    Senkron requests çağrısını run_in_threadpool ile sarmalar.\n    """',
        '    """\n    Generates a viral cloning concept using Groq Llama-3.\n    Wraps the synchronous requests call with run_in_threadpool.\n    """',
    ),
    (
        '    """\n    Predictive Intelligence bağlamı oluşturur.\n    Tier, zaman penceresi, hız, penetrasyon ve yorum sinyallerini AI\'ya açıklar.\n    Anti-hallüsinasyon: yorum sinyali yoksa AI\'ya açıkça bildirilir.\n    """',
        '    """\n    Builds Predictive Intelligence context.\n    Explains tier, time window, velocity, penetration, and comment signals to the AI.\n    Anti-hallucination: if there are no comment signals, the AI is explicitly informed.\n    """',
    ),
    (
        '    """\n    İki persona paralel çalışır (asyncio.gather), ardından Hakem AI karar verir.\n    Çıktı kesinlikle ayrıştırılabilir JSON dict olmalı — aksi hâlde HTTPException(500).\n    """',
        '    """\n    Two personas run in parallel (asyncio.gather), then the Judge AI makes the decision.\n    Output must be a parseable JSON dict — otherwise HTTPException(500) is raised.\n    """',
    ),
    (
        '    """\n    A/B Test Simülatörü — Multi-Agent Debate Endpoint.\n    Persona A (Eleştirmen) + Persona B (Büyücü) paralel çalışır.\n    Hakem AI en iyi fikri seçer/harmanlayarak JSON döner.\n\n    Beklenen JSON body: { "url": "...", "videoId": "...", "title": "...", "channel": "...", "thumbnail": "..." }\n    Çıktı: { "success": true, "debate": { eleştirmen_fikri, buyucu_fikri, kazanan_baslik, kazanan_kanca, kazanan_thumbnail } }\n    """',
        '    """\n    A/B Test Simulator — Multi-Agent Debate Endpoint.\n    Persona A (Critic) + Persona B (Mage) run in parallel.\n    Judge AI selects/blends the best idea and returns JSON.\n\n    Expected JSON body: { "url": "...", "videoId": "...", "title": "...", "channel": "...", "thumbnail": "..." }\n    Output: { "success": true, "debate": { eleştirmen_fikri, buyucu_fikri, kazanan_baslik, kazanan_kanca, kazanan_thumbnail } }\n    """',
    ),
    (
        '    """JSON bloğunu çıkar ve parse et. Hata varsa HTTPException(500) fırlat."""',
        '    """Extract and parse the JSON block. Raise HTTPException(500) on error."""',
    ),
    (
        '    """\n    Kullanıcının kendi nişine uygun, şu an YouTube\'da patlamakta olan 3 adet\n    \'Aykırı\' videoyu tespit eder.\n    - Kullanıcının kanal konseptine göre 3 farklı niş sorgusu (Groq ile) üretilir.\n    - 3 sorgu PARALEL çalıştırılır (asyncio.gather).\n    - Son 48 saatte yüklenmiş videolar önceliklendirilir.\n    - Kendi kanalı videoları (dinamik öz-karşılaştırma) atlanır.\n    - En yüksek velocity\'ye sahip 3 video seçilir.\n    """',
        '    """\n    Detects 3 \'Outlier\' videos currently trending on YouTube\n    that match the user\'s own niche.\n    - 3 different niche queries (via Groq) are generated based on the user\'s channel concept.\n    - 3 queries run IN PARALLEL (asyncio.gather).\n    - Videos uploaded in the last 48 hours are prioritized.\n    - The user\'s own channel videos are skipped (dynamic self-filtering).\n    - The 3 videos with the highest velocity are selected.\n    """',
    ),
    (
        '    """\n    Chrome eklentisinden gelen video verilerini karşılar.\n    1. Transcript çeker (youtube-transcript-api, thread-pool içinde)\n    2. Groq ile viral konsept üretir\n    3. Sonucu JSON olarak döner\n    """',
        '    """\n    Receives video data from the Chrome extension.\n    1. Fetches transcript (youtube-transcript-api, inside thread-pool)\n    2. Generates viral concept with Groq\n    3. Returns the result as JSON\n    """',
    ),

    # ── arial font docstring (multi-line) ────────────────────────────────────
    (
        '    """\n    arial.ttf / arialbd.ttf için arama sırası:\n      1. BASE_DIR (proje klasörü)\n      2. Windows sistem font klasörü  (C:/Windows/Fonts)\n      3. Helvetica fallback\n    """',
        '    """\n    Search order for arial.ttf / arialbd.ttf:\n      1. BASE_DIR (project folder)\n      2. Windows system fonts folder (C:/Windows/Fonts)\n      3. Helvetica fallback\n    """',
    ),

    # ── log_exception crash log ──────────────────────────────────────────────
    (
        '        f.write(f"\\n--- HATA ZAMANI: {time.ctime()} ---\\n")',
        '        f.write(f"\\n--- ERROR TIME: {time.ctime()} ---\\n")',
    ),

    # ── stdout redirect error ────────────────────────────────────────────────
    (
        '    app_logger.error(f"Hata [stdout_redirect]: {str(e)}", exc_info=True)',
        '    app_logger.error(f"Error [stdout_redirect]: {str(e)}", exc_info=True)',
    ),

    # ── _load_pdf_lang print ─────────────────────────────────────────────────
    (
        '        print(f"translations.xlsx okunamadı, fallback boş dict: {e}")',
        '        print(f"translations.xlsx could not be read, falling back to empty dict: {e}")',
    ),

    # ── GPU codec detect ─────────────────────────────────────────────────────
    (
        '                print(f"✅ GPU Codec bulundu: {codec} ({brand})")',
        '                print(f"✅ GPU Codec found: {codec} ({brand})")',
    ),
    (
        '    print("ℹ️ GPU codec bulunamadı, CPU (libx264) kullanılacak.")',
        '    print("ℹ️ No GPU codec found, falling back to CPU (libx264).")',
    ),

    # ── check_ffmpeg error ───────────────────────────────────────────────────
    (
        '        app_logger.error(f"Hata [check_ffmpeg]: FFmpeg bulunamadı veya çalıştırılamadı. {e}")',
        '        app_logger.error(f"Error [check_ffmpeg]: FFmpeg not found or could not be executed. {e}")',
    ),

    # ── detect_system_capabilities comment + log ─────────────────────────────
    (
        '    # RAM (platform bağımsız, psutil olmadan)',
        '    # RAM (platform-independent, without psutil)',
    ),
    (
        '    # Fast mode: 8+ çekirdek veya GPU codec varsa agresif ayarlar kullan',
        '    # Fast mode: use aggressive settings if 8+ cores or GPU codec is available',
    ),
    (
        '        f"🖥️ Sistem profili: CPU={cpu_count} çekirdek, RAM={SYSTEM_CAPS[\'ram_gb\']}GB, "',
        '        f"🖥️ System profile: CPU={cpu_count} cores, RAM={SYSTEM_CAPS[\'ram_gb\']}GB, "',
    ),

    # ── cleanup_temp_videos errors ───────────────────────────────────────────
    (
        '                    app_logger.warning(f"Hata [cleanup_temp_videos]: {f} silinemedi: {e}")',
        '                    app_logger.warning(f"Error [cleanup_temp_videos]: {f} could not be deleted: {e}")',
    ),
    (
        '        app_logger.error(f"Hata [cleanup_temp_videos] genel hata: {e}")',
        '        app_logger.error(f"Error [cleanup_temp_videos] general error: {e}")',
    ),

    # ── validation_exception_handler body ────────────────────────────────────
    (
        '        body_str = "<okunamadı>"',
        '        body_str = "<unreadable>"',
    ),
    (
        '        f"  Gelen body: {body_str}\\n"',
        '        f"  Incoming body: {body_str}\\n"',
    ),
    (
        '        f"  Validation hataları: {exc.errors()}"',
        '        f"  Validation errors: {exc.errors()}"',
    ),
    (
        '            "error": "Gönderilen veri formatı hatalı.",',
        '            "error": "The submitted data format is invalid.",',
    ),

    # ── crypto_exception_handler ─────────────────────────────────────────────
    (
        '    app_logger.error(f"[CRYPTO_ERROR] endpoint={request.url.path} mesaj={str(exc)}")',
        '    app_logger.error(f"[CRYPTO_ERROR] endpoint={request.url.path} message={str(exc)}")',
    ),

    # ── global_error_handler ─────────────────────────────────────────────────
    (
        '        # Try to extract the user ID',
        '        # Try to extract the user ID',
    ),
    (
        '                "error": f"Bir sorun oluştu. Hata kodu: {error_code}. Lütfen bu kodu destek ekibine gönderin.",',
        '                "error": f"Something went wrong. Error code: {error_code}. Please send this code to the support team.",',
    ),

    # ── google_auth_url ───────────────────────────────────────────────────────
    (
        '            return {"error": "Google Client ID ayarlanmamış. Ayarlar sayfasından ekleyin."}',
        '            return {"error": "Google Client ID is not configured. Please add it from the Settings page."}',
    ),
    (
        '        app_logger.error(f"Google auth URL oluşturma hatası: {e}", exc_info=True)',
        '        app_logger.error(f"Google auth URL creation error: {e}", exc_info=True)',
    ),
    (
        '        return {"error": "Google auth URL oluşturulamadı."}',
        '        return {"error": "Google auth URL could not be created."}',
    ),

    # ── google_auth_callback ─────────────────────────────────────────────────
    (
        '        return HTMLResponse("<h2>Hata: Yetkilendirme kodu alınamadı.</h2>")',
        '        return HTMLResponse("<h2>Error: Authorization code could not be retrieved.</h2>")',
    ),
    (
        '                return HTMLResponse("<h2>Google OAuth yapılandırması eksik.</h2>")',
        '                return HTMLResponse("<h2>Google OAuth configuration is incomplete.</h2>")',
    ),
    (
        '                app_logger.error(f"Google token exchange hatası: {token_resp.text}")',
        '                app_logger.error(f"Google token exchange error: {token_resp.text}")',
    ),
    (
        '                return HTMLResponse("<h2>Google ile giriş başarısız.</h2>")',
        '                return HTMLResponse("<h2>Sign-in with Google failed.</h2>")',
    ),
    (
        '                return HTMLResponse("<h2>Google kullanıcı bilgileri alınamadı.</h2>")',
        '                return HTMLResponse("<h2>Google user information could not be retrieved.</h2>")',
    ),
    (
        '            # Create unique username',
        '            # Create unique username',
    ),
    (
        '        # Create session and redirect',
        '        # Create session and redirect',
    ),
    (
        '        app_logger.info(f"✅ Google login başarılı: user_id={user_id}, username={username}")',
        '        app_logger.info(f"✅ Google login successful: user_id={user_id}, username={username}")',
    ),
    (
        '        session_json_safe = _json.dumps(session_json)  # çift tırnakla sarılı JSON string',
        '        session_json_safe = _json.dumps(session_json)  # JSON string wrapped in double quotes',
    ),
    (
        '            <p>Giriş yapılıyor...</p>',
        '            <p>Logging in...</p>',
    ),
    (
        '        app_logger.error(f"Google auth callback hatası: {e}", exc_info=True)',
        '        app_logger.error(f"Google auth callback error: {e}", exc_info=True)',
    ),
    (
        '        return HTMLResponse("<h2>Google ile giriş sırasında bir hata oluştu.</h2>")',
        '        return HTMLResponse("<h2>An error occurred during Google sign-in.</h2>")',
    ),

    # ── save_google_oauth ─────────────────────────────────────────────────────
    (
        '            return {"success": False, "error": "Client ID ve Secret boş olamaz."}',
        '            return {"success": False, "error": "Client ID and Secret cannot be empty."}',
    ),
    (
        '        app_logger.error(f"Google OAuth ayarları kayıt hatası: {e}")',
        '        app_logger.error(f"Google OAuth settings save error: {e}")',
    ),
    (
        '        return {"success": False, "error": "Kayıt hatası."}',
        '        return {"success": False, "error": "Save error."}',
    ),

    # ── register endpoint ─────────────────────────────────────────────────────
    (
        '            return {"error": "Kullanıcı adı en az 3 karakter olmalıdır."}',
        '            return {"error": "Username must be at least 3 characters long."}',
    ),
    (
        '            return {"error": "Şifre en az 6 karakter olmalıdır."}',
        '            return {"error": "Password must be at least 6 characters long."}',
    ),
    (
        '            return {"error": "Kullanıcı adında boşluk olamaz."}',
        '            return {"error": "Username cannot contain spaces."}',
    ),
    (
        '            return {"error": "Geçerli bir email adresi girin."}',
        '            return {"error": "Please enter a valid email address."}',
    ),
    (
        '                return {"error": "Bu kullanıcı adı zaten kullanılıyor."}',
        '                return {"error": "This username is already taken."}',
    ),
    (
        '            # Generate verification code',
        '            # Generate verification code',
    ),
    (
        '        print(f"MAIL GÖNDERİLİYOR: {email}, kod: {code}")',
        '        print(f"SENDING EMAIL: {email}, code: {code}")',
    ),
    (
        '        return {"error": "Kayıt sırasında beklenmeyen bir hata oluştu."}',
        '        return {"error": "An unexpected error occurred during registration."}',
    ),

    # ── login endpoint ────────────────────────────────────────────────────────
    (
        '            return {"error": "Kullanıcı adı ve şifre boş olamaz."}',
        '            return {"error": "Username and password cannot be empty."}',
    ),
    (
        '            return {"error": "Kullanıcı bulunamadı."}',
        '            return {"error": "User not found."}',
    ),
    (
        '            return {"error": "Bu hesaba giriş yapılamaz."}',
        '            return {"error": "Cannot sign in to this account."}',
    ),
    (
        '            return {"error": "Şifre yanlış."}',
        '            return {"error": "Incorrect password."}',
    ),
    (
        '        return {"error": "Giriş sırasında beklenmeyen bir hata oluştu."}',
        '        return {"error": "An unexpected error occurred during login."}',
    ),

    # ── verify_email endpoint ─────────────────────────────────────────────────
    (
        '            return {"error": "Eksik bilgi."}',
        '            return {"error": "Missing information."}',
    ),
    (
        '                return {"error": "Kod yanlış."}',
        '                return {"error": "Incorrect code."}',
    ),
    (
        '                return {"error": "Bu kod zaten kullanılmış."}',
        '                return {"error": "This code has already been used."}',
    ),
    (
        '                return {"error": "Kodun süresi dolmuş. Tekrar kayıt ol."}',
        '                return {"error": "The code has expired. Please register again."}',
    ),
    (
        '        return {"error": "Doğrulama sırasında hata oluştu."}',
        '        return {"error": "An error occurred during verification."}',
    ),

    # ── resend_verification endpoint ──────────────────────────────────────────
    (
        '        return {"error": "Kod gönderilemedi."}',
        '        return {"error": "Code could not be sent."}',
    ),

    # ── get_profile ───────────────────────────────────────────────────────────
    (
        '        return {"error": "Profil yüklenirken hata oluştu."}',
        '        return {"error": "An error occurred while loading the profile."}',
    ),

    # ── get_analysis_by_id ────────────────────────────────────────────────────
    (
        '            return {"error": "Analiz bulunamadı."}',
        '            return {"error": "Analysis not found."}',
    ),
    (
        '        return {"error": "Analiz yüklenirken hata oluştu."}',
        '        return {"error": "An error occurred while loading the analysis."}',
    ),

    # ── delete_analysis ───────────────────────────────────────────────────────
    (
        '        return {"success": False, "error": "Silme işlemi başarısız."}',
        '        return {"success": False, "error": "Delete operation failed."}',
    ),

    # ── set_gemini_key ────────────────────────────────────────────────────────
    (
        '    if key == "(kayıtlı)":\n        return {"success": True}',
        '    if key == "(saved)":\n        return {"success": True}',
    ),
    (
        '        return {"success": False, "error": "Geçersiz Gemini API Anahtarı"}',
        '        return {"success": False, "error": "Invalid Gemini API Key"}',
    ),
    (
        '        return {"success": False, "error": "Gemini API ile bağlantı kurulamadı"}',
        '        return {"success": False, "error": "Could not connect to Gemini API"}',
    ),

    # ── content_finder ────────────────────────────────────────────────────────
    (
        '            return {"error": "Lütfen aranacak bir kelime veya konsept girin."}',
        '            return {"error": "Please enter a keyword or concept to search for."}',
    ),
    (
        '            return {"error": "yt-dlp yüklü değil, arama yapılamıyor."}',
        '            return {"error": "yt-dlp is not installed, search is unavailable."}',
    ),
    (
        '                    return {"error": f"\'{keyword}\' için arama sonucu bulunamadı."}',
        '                    return {"error": f"No search results found for \'{keyword}\'."}',
    ),
    (
        "            app_logger.debug(f\"Hata [content_finder date parse]: {e}\")",
        '            app_logger.debug(f"Error [content_finder date parse]: {e}")',
    ),
    (
        "            return {\"error\": f\"YouTube araması sırasında hata: {str(e)[:100]}\"}",
        '            return {"error": f"Error during YouTube search: {str(e)[:100]}"}',
    ),
    (
        '            return {"error": "Arama sonucunda hiç video bulunamadı."}',
        '            return {"error": "No videos found in search results."}',
    ),
    (
        '        app_logger.error(f"Hata [content_finder db save]: {e}")',
        '        app_logger.error(f"Error [content_finder db save]: {e}")',
    ),
    (
        '        return {"error": "İçerik bulucu çalıştırılırken sunucu hatası oluştu."}',
        '        return {"error": "A server error occurred while running the content finder."}',
    ),

    # ── analyse upload ────────────────────────────────────────────────────────
    (
        '            raise HTTPException(status_code=400, detail="Yüklenen video dosyası seçilmedi.")',
        '            raise HTTPException(status_code=400, detail="No uploaded video file selected.")',
    ),
    (
        '        # --- NON-BLOCKING: Dosya kopyalama (ağır I/O) ---',
        '        # --- NON-BLOCKING: File copy (heavy I/O) ---',
    ),
    (
        '        # --- NON-BLOCKING: Ağır CPU/IO analiz işlemleri ---',
        '        # --- NON-BLOCKING: Heavy CPU/IO analysis operations ---',
    ),
    (
        '        # --- NON-BLOCKING: Sahne değişimi ve hareket analizi (Aşama 3) ---',
        '        # --- NON-BLOCKING: Scene transition and motion analysis (Phase 3) ---',
    ),
    (
        "                email_sent = True  # SMTP yapılandırması mevcut, gönderim tetiklenebilir",
        "                email_sent = True  # SMTP configuration present, dispatch can be triggered",
    ),
    (
        '                app_logger.info(f"SMTP hazır, analiz raporu e-postaya gönderilebilir: user={user_email}")',
        '                app_logger.info(f"SMTP ready, analysis report can be sent by email: user={user_email}")',
    ),

    # ── FFmpeg not found ──────────────────────────────────────────────────────
    (
        '            return {"error": "FFmpeg sistemde bulunamadı."}',
        '            return {"error": "FFmpeg was not found on this system."}',
    ),
    (
        '            return {"error": "Video dosyası bulunamadı. Lütfen videoyu tekrar analiz edin."}',
        '            return {"error": "Video file not found. Please re-analyse the video."}',
    ),
    (
        '        # GPU codec\'e göre parametreleri ayarla',
        '        # Adjust parameters based on GPU codec',
    ),
    (
        '            print(f"FFmpeg Hatası Detayı: {process.stderr}")',
        '            print(f"FFmpeg Error Details: {process.stderr}")',
    ),
    (
        '            return {"error": f"Kesme işlemi başarısız: {process.stderr[:100]}"}',
        '            return {"error": f"Cut operation failed: {process.stderr[:100]}"}',
    ),
    (
        '        return {"error": f"Sistem Hatası: {str(e)}"}',
        '        return {"error": f"System Error: {str(e)}"}',
    ),

    # ── language fallback comment ─────────────────────────────────────────────
    (
        '    # Geçersiz dil kodu gelirse Türkçe\'ye düş',
        "    # Fall back to Turkish if an invalid language code is received",
    ),

    # ── PDF generation comments ───────────────────────────────────────────────
    (
        '    # video_description ve video_tags DB\'den al (yoksa competitor_data içinden çıkar)',
        "    # Get video_description and video_tags from DB (fall back to extracting from competitor_data)",
    ),
    (
        "    # competitor_data'dan da açıklama ve etiket almayı dene",
        "    # Also try to get description and tags from competitor_data",
    ),
    (
        '    # ── APA Stil Tanımları ──',
        '    # ── APA Style Definitions ──',
    ),
    (
        '    # Kapak başlığı (ortalı, büyük)',
        '    # Cover title (centered, large)',
    ),
    (
        '    # Üst başlık — TAMAMEN BÜYÜK HARF',
        '    # Top heading — ALL CAPS',
    ),
    (
        '    # Alt başlık — İlk Harf Büyük',
        '    # Sub-heading — Title Case',
    ),
    (
        '    # Bölüm sayacı',
        '    # Section counter',
    ),
    (
        '        # İlk harfleri büyük yap',
        '        # Capitalize first letters',
    ),
    (
        '    # ince ayırıcı çizgi',
        '    # thin separator line',
    ),
    (
        '    # ── 2. Sektör Standartları ──',
        '    # ── 2. Industry Standards ──',
    ),
    (
        '    # ── SEO / Thumbnail Denge Uyarısı ──',
        '    # ── SEO / Thumbnail Balance Warning ──',
    ),
    (
        '    # ── 3. SEO / Thumbnail Denge Uyarısı ──',
        '    # ── 3. SEO / Thumbnail Balance Warning ──',
    ),
    (
        '    # Durum 1: SEO güçlü ama Thumbnail zayıf → arama çıkar, tıklanmaz',
        '    # Case 1: Strong SEO but weak Thumbnail → shows in search, not clicked',
    ),
    (
        '    # ── 4. İçerik Tutarlılık Kontrolü ──',
        '    # ── 4. Content Consistency Check ──',
    ),
    (
        '    # ── TABLO 2: Görsel Kalite Metrikleri ──',
        '    # ── TABLE 2: Visual Quality Metrics ──',
    ),
    (
        '    # ── TABLO 3: Heyecan Katsayısı Özeti ──',
        '    # ── TABLE 3: Excitement Score Summary ──',
    ),
    (
        '    # ── 6. Kıyaslama Tablosu ──',
        '    # ── 6. Comparison Table ──',
    ),
    (
        '    # ── Süre dipnotu ──',
        '    # ── Duration footnote ──',
    ),

    # ── PDF inline fallback dict ──────────────────────────────────────────────
    (
        '        "emotion_title": "THUMBNAIL DUYGU ANALİZİ",',
        '        "emotion_title": "THUMBNAIL EMOTION ANALYSIS",',
    ),
    (
        '        "emotion": "Duygu", "score": "Skor (%)", "dominant": "Baskın",',
        '        "emotion": "Emotion", "score": "Score (%)", "dominant": "Dominant",',
    ),
    (
        '        "no_face": "Thumbnail\'de yüz tespit edilemedi.",',
        '        "no_face": "No face detected in thumbnail.",',
    ),
    (
        '        "visual_title": "GÖRSEL KALİTE METRİKLERİ",',
        '        "visual_title": "VISUAL QUALITY METRICS",',
    ),
    (
        '        "metric": "Metrik", "value": "Değer", "status": "Durum",',
        '        "metric": "Metric", "value": "Value", "status": "Status",',
    ),
    (
        '        "contrast": "Kontrast (Michelson)", "vibrant": "Canlı Renk Uyumu",',
        '        "contrast": "Contrast (Michelson)", "vibrant": "Vibrant Color Harmony",',
    ),
    (
        '        "text_space": "Metin Alanı Skoru", "brightness": "Parlaklık",',
        '        "text_space": "Text Area Score", "brightness": "Brightness",',
    ),
    (
        '        "excellent": "Mükemmel", "good": "İyi", "low": "Düşük", "medium": "Orta",',
        '        "excellent": "Excellent", "good": "Good", "low": "Low", "medium": "Medium",',
    ),
    (
        '        "excitement_title": "HEYECAN KATSAYISI ÖZETİ (Excitement Score)",',
        '        "excitement_title": "EXCITEMENT SCORE SUMMARY",',
    ),
    (
        '        "segment": "Segment", "time_range": "Zaman Aralığı",',
        '        "segment": "Segment", "time_range": "Time Range",',
    ),
    (
        '        "excitement": "Heyecan", "audio": "Ses Yoğ.", "cut": "Kesim Yoğ.",',
        '        "excitement": "Excitement", "audio": "Audio Den.", "cut": "Cut Den.",',
    ),
    (
        '        "motion": "Hareket Yoğ.", "no_segments": "Viral segment tespit edilemedi.",',
        '        "motion": "Motion Den.", "no_segments": "No viral segments detected.",',
    ),

    # ── competitor_data JSON comments ─────────────────────────────────────────
    (
        '    # competitor_data JSON\'ından ek verileri çıkar',
        '    # Extract additional data from competitor_data JSON',
    ),

    # ── gaze text ─────────────────────────────────────────────────────────────
    (
        '        gaze_txt = "👀 Kameraya bakıyor ✅" if lang == "tr" else "👀 Looking at camera ✅" if lang == "en" else "👀 Mirando a cámara ✅"',
        '        gaze_txt = "👀 Looking at camera ✅" if lang == "en" else "👀 Mirando a cámara ✅" if lang == "es" else "👀 Kameraya bakıyor ✅"',
    ),
    (
        '            gaze_txt = "👀 Kameraya bakmıyor" if lang == "tr" else "👀 Not looking at camera" if lang == "en" else "👀 No mira a cámara"',
        '            gaze_txt = "👀 Not looking at camera" if lang == "en" else "👀 No mira a cámara" if lang == "es" else "👀 Kameraya bakmıyor"',
    ),

    # ── PDF positives ─────────────────────────────────────────────────────────
    (
        '        positives.append(f"SEO optimizasyonu çok başarılı (Skor: {seo:.1f}/10)")',
        '        positives.append(f"SEO optimization is very strong (Score: {seo:.1f}/10)")',
    ),
    (
        '        positives.append(f"Thumbnail kontrastı mükemmel ({cr:.2f}), dikkat çekici")',
        '        positives.append(f"Thumbnail contrast is excellent ({cr:.2f}), eye-catching")',
    ),

    # ── channel not found HTTP ────────────────────────────────────────────────
    (
        '            raise HTTPException(status_code=404, detail="Kanal bulunamadı")',
        '            raise HTTPException(status_code=404, detail="Channel not found")',
    ),

    # ── set_smtp saved key guard ──────────────────────────────────────────────
    (
        '    if key.strip() == "(kayıtlı)":\n        return {"success": True}',
        '    if key.strip() == "(saved)":\n        return {"success": True}',
    ),

    # ── SMTP email/password validation ───────────────────────────────────────
    (
        '            return {"success": False, "error": "Email ve şifre boş olamaz."}',
        '            return {"success": False, "error": "Email and password cannot be empty."}',
    ),
    (
        '        return {"success": False, "error": "Kayıt hatası."}',
        '        return {"success": False, "error": "Save error."}',
    ),

    # ── session ownership comment ─────────────────────────────────────────────
    (
        '        # Oturumun bu kullanıcıya ait olduğunu doğrula',
        '        # Verify that this session belongs to this user',
    ),

    # ── Groq API key missing ──────────────────────────────────────────────────
    (
        '            return {"error": "NO_KEY", "details": "API anahtarı bulunamadı. Lütfen Groq API anahtarını gir."}',
        '            return {"error": "NO_KEY", "details": "API key not found. Please enter your Groq API key."}',
    ),

    # ── file_context ──────────────────────────────────────────────────────────
    (
        '                    file_context = f"Kullanıcının yüklediği dosya ({file_name}):\\n{decoded[:3000]}"',
        '                    file_context = f"File uploaded by user ({file_name}):\\n{decoded[:3000]}"',
    ),

    # ── title_keywords list ───────────────────────────────────────────────────
    (
        '    title_keywords = ["başlık", "title", "isim", "name", "ne yazayım", "nasıl adlandır", "başlık öner", "başlık yaz"]',
        '    title_keywords = ["başlık", "title", "isim", "name", "ne yazayım", "nasıl adlandır", "başlık öner", "başlık yaz"]  # bilingual intent keywords — do not translate',
    ),

    # ── memory_block comment ──────────────────────────────────────────────────
    (
        '    # --- HAFIZA SİSTEMİ: Memory block oluştur ---',
        '    # --- MEMORY SYSTEM: Build memory block ---',
    ),

    # ── Groq error responses ──────────────────────────────────────────────────
    (
        '                return {"error": "INVALID_KEY", "details": "API anahtarın geçersiz."}',
        '                return {"error": "INVALID_KEY", "details": "Your API key is invalid."}',
    ),
    (
        '                return {"error": "QUOTA", "details": "Sınır aşıldı. Lütfen biraz bekleyin."}',
        '                return {"error": "QUOTA", "details": "Quota exceeded. Please wait a moment."}',
    ),
    (
        '            return {"error": "API_ERROR", "details": f"Groq hatası: {err}"}',
        '            return {"error": "API_ERROR", "details": f"Groq error: {err}"}',
    ),
    (
        '        return {"error": "TIMEOUT", "details": "Sunucu yanıt vermedi. Tekrar dene."}',
        '        return {"error": "TIMEOUT", "details": "Server did not respond. Please try again."}',
    ),
    (
        '        return {"error": "NETWORK_ERROR", "details": f"Bağlantı hatası: {str(e)}"}',
        '        return {"error": "NETWORK_ERROR", "details": f"Connection error: {str(e)}"}',
    ),

    # ── send_report ───────────────────────────────────────────────────────────
    (
        '            return {"success": False, "error": "Kullanıcı e-postası bulunamadı."}',
        '            return {"success": False, "error": "User email not found."}',
    ),
    (
        '        # Önce PDF\'i oluştur (export_pdf endpoint\'ini simüle et)',
        "        # First generate the PDF (simulating the export_pdf endpoint)",
    ),
    (
        '            # PDF yoksa yerel URL\'den çek',
        "            # If PDF doesn't exist, fetch from local URL",
    ),
    (
        '            return {"success": True, "message": "Rapor e-postanıza gönderildi!"}',
        '            return {"success": True, "message": "Report sent to your email!"}',
    ),
    (
        '            return {"success": False, "error": "SMTP ayarları eksik veya gönderim başarısız."}',
        '            return {"success": False, "error": "SMTP settings are incomplete or sending failed."}',
    ),

    # ── translations endpoint ─────────────────────────────────────────────────
    (
        '    # Arama sırası: BUNDLE_DIR → APP_DIR → BASE_DIR (PyInstaller ve dev modu uyumlu)',
        '    # Search order: BUNDLE_DIR → APP_DIR → BASE_DIR (compatible with PyInstaller and dev mode)',
    ),
    (
        '            f"[translations] translations.xlsx bulunamadı! "',
        '            f"[translations] translations.xlsx not found! "',
    ),
    (
        "            'error': f\"translations.xlsx bulunamadı. Aranan yollar: {tried}\",",
        "            'error': f\"translations.xlsx not found. Searched paths: {tried}\",",
    ),
    (
        '        app_logger.info(f"[translations] Yükleniyor: {xlsx_path}")',
        '        app_logger.info(f"[translations] Loading: {xlsx_path}")',
    ),
    (
        '            f"[translations] ✅ Yüklendi: {len(result.get(\'tr\', {}))} anahtar "',
        '            f"[translations] ✅ Loaded: {len(result.get(\'tr\', {}))} keys "',
    ),
    (
        '            f"Dosya: {xlsx_path} | Hata türü: {type(e).__name__} | Detay: {e}",',
        '            f"File: {xlsx_path} | Error type: {type(e).__name__} | Detail: {e}",',
    ),
    (
        "            'error': f\"Çeviri dosyası okunamadı: {type(e).__name__}: {e}\",",
        "            'error': f\"Translation file could not be read: {type(e).__name__}: {e}\",",
    ),

    # ── VIRAL CLONING ENGINE section header ───────────────────────────────────
    (
        '#   VİRAL KLONLAMA MOTORU — Chrome Eklentisi Entegrasyonu',
        '#   VIRAL CLONING ENGINE — Chrome Extension Integration',
    ),
    (
        '    # 1. Aşama: YouTubeTranscriptApi ile tüm altyazıları çek (İlk tercih)',
        '    # Phase 1: Fetch all subtitles with YouTubeTranscriptApi (first choice)',
    ),
    (
        '    last_api_error = "YouTubeTranscriptApi kullanılabilir değil"  # NameError koruyası',
        '    last_api_error = "YouTubeTranscriptApi not available"  # NameError guard',
    ),
    (
        '    # 2. Aşama: youtube-transcript-api hata verirse (örn: XML Parse Error), yt-dlp ile ZORLA ÇEK',
        '    # Phase 2: If youtube-transcript-api fails (e.g. XML Parse Error), FORCE fetch with yt-dlp',
    ),
    (
        '                # yt-dlp de altyazı bulamadıysa, ilk kütüphanenin hatasını dön',
        '                # If yt-dlp also cannot find subtitles, return the first library\'s error',
    ),
    (
        '            # Öncelikle istediğimiz dilleri ara',
        '            # First search for the languages we want',
    ),
    (
        '            # YouTube genellikle JSON3 formatında subtitle döner',
        '            # YouTube usually returns subtitles in JSON3 format',
    ),
    (
        '            # VTT formatı ise temizle',
        '            # If VTT format, clean it',
    ),
    (
        '                # VTT içindeki <c>, <00:00:00.000> gibi tagları regex ile sil',
        '                # Remove tags like <c>, <00:00:00.000> from VTT using regex',
    ),
    (
        '        # Son çare olarak hataları döndür',
        '        # Return errors as a last resort',
    ),
    (
        '        raise ValueError(f"Altyazı çekilemedi. API Hatası: {last_api_error} | Yedek Motor Hatası: {e}")',
        '        raise ValueError(f"Subtitle could not be fetched. API Error: {last_api_error} | Fallback Engine Error: {e}")',
    ),

    # ── thumbnail rule comments ───────────────────────────────────────────────
    (
        '# ── Thumbnail Kuralı: İçerik tipine göre dinamik oluştur ─────────────────────',
        '# ── Thumbnail Rule: Build dynamically based on content type ───────────────────',
    ),
    (
        '# BUG FIX: Oyun/gaming kanalları için insan yüzü YASAK direktifi.',
        '# BUG FIX: Human face FORBIDDEN directive for gaming channels.',
    ),
    (
        '# Ana AI (chat) promptu bu kuralı içeriyordu ama _call_groq_clone içine',
        '# The main AI (chat) prompt contained this rule but it was not cascading',
    ),
    (
        '# cascade etmiyordu — bu yüzden halüsinasyon üretiliyordu. Artık düzeltildi.',
        '# into _call_groq_clone — causing hallucinations. Now fixed.',
    ),

    # ── BabaClutch chaos metric ───────────────────────────────────────────────
    (
        '    # 1. Rage Yoğunluğu (0-10)',
        '    # 1. Rage Intensity (0-10)',
    ),
    (
        '    # 2. Tempo Varyansı (0-10)',
        '    # 2. Tempo Variance (0-10)',
    ),
    (
        '    if len(lengths) > 1: # Fail-Fast: ZeroDivisionError / ValueError koruması',
        '    if len(lengths) > 1: # Fail-Fast: ZeroDivisionError / ValueError guard',
    ),
    (
        '    # 3. Başlık Agresifliği (0-10)',
        '    # 3. Title Aggressiveness (0-10)',
    ),
    (
        '    # BabaClutch Hükmü',
        '    # BabaClutch Verdict',
    ),

    # ── competitor fetch comments ─────────────────────────────────────────────
    (
        "        # STRES TESTİ FIX #6: yt-dlp rate-limit ve IP ban koruması",
        "        # STRESS TEST FIX #6: yt-dlp rate-limit and IP ban protection",
    ),
    (
        "        # Socketleri çok çabuk açmak 429'u tetikler; küçük bir sleep eklenebilir.",
        "        # Opening sockets too quickly triggers 429; a small sleep may be added.",
    ),
    (
        "        'sleep_interval': 1,        # istekler arası minimum 1sn bekle",
        "        'sleep_interval': 1,        # minimum 1s wait between requests",
    ),
    (
        "    # Exponential Backoff: 429 veya geçici ağ hatasında 3 kez dene (1s → 3s → 9s)",
        "    # Exponential Backoff: retry 3 times on 429 or transient network error (1s → 3s → 9s)",
    ),
    (
        "            break  # Başarılı → döngüden çık",
        "            break  # Success → exit loop",
    ),
    (
        '                    f"[Kanal Savaşları] yt-dlp hata (deneme {attempt+1}/3): {e} | "',
        '                    f"[Channel Battles] yt-dlp error (attempt {attempt+1}/3): {e} | "',
    ),
    (
        "                # Kalıcı hata veya 3. deneme: fırlat",
        "                # Permanent error or 3rd attempt: raise",
    ),
    (
        '                        "YouTube rate-limit uyguladı (HTTP 429). "',
        '                        "YouTube applied rate-limiting (HTTP 429). "',
    ),
    (
        '                        "Kanal Savaşları birkaç dakika içinde tekrar denenebilir. "',
        '                        "Channel Battles can be retried in a few minutes. "',
    ),
    (
        '                        "Çok sık tarama yapmak IP ban riskini artırır."',
        '                        "Scanning too frequently increases the risk of an IP ban."',
    ),
    (
        '                raise ValueError(f"Kanal verileri çekilemedi: {e}")',
        '                raise ValueError(f"Channel data could not be fetched: {e}")',
    ),
    (
        "        # Tüm denemeler başarısız",
        "        # All attempts failed",
    ),
    (
        '        raise ValueError(f"Kanal verileri 3 denemede de çekilemedi: {last_error}")',
        '        raise ValueError(f"Channel data could not be fetched in 3 attempts: {last_error}")',
    ),
    (
        '        raise ValueError("Kanal videoları bulunamadı.")',
        '        raise ValueError("Channel videos not found.")',
    ),
    (
        "    # Eğer extract_flat view_count'ları getirmediyse (None geldiyse),",
        "    # If extract_flat did not return view_counts (returned None),",
    ),
    (
        '    # İlk 3 videonun meta verisini tekil olarak çekiyoruz (Daha hızlı ve stabil)',
        '    # Fetch the metadata of the first 3 videos individually (faster and more stable)',
    ),

    # ── Transcript & Chaos Metric section comment ─────────────────────────────
    (
        '    # Transcript Çekimi ve Kaos Metriği',
        '    # Transcript Retrieval and Chaos Metric',
    ),

    # ── Prophet picks comments ────────────────────────────────────────────────
    (
        '#   PROPHET\'S PICK — Otomatik Viral Öneri Sistemi',
        "#   PROPHET'S PICK — Automatic Viral Recommendation System",
    ),
    (
        '#   BabaClutch nişine (Oyun/Kaos) uygun, şu an patlamakta olan',
        '#   Detects 3 "Outlier" videos currently trending on YouTube',
    ),
    (
        '#   3 adet "Aykırı" videoyu otomatik olarak tespit eder.',
        '#   that match the BabaClutch niche (Gaming/Chaos).',
    ),
    (
        '#   Mevcut extract_rabbit_hole_sync modülünü kullanır (KISS).',
        '#   Uses the existing extract_rabbit_hole_sync module (KISS principle).',
    ),
    (
        '#   3 sorgu asyncio ile PARALEL çalışır → maks ~2sn yükleme.',
        '#   3 queries run in PARALLEL via asyncio → max ~2s load time.',
    ),
    (
        '        if not api_key: return v, True # API key yoksa mecburen geçir',
        '        if not api_key: return v, True # No API key, pass through',
    ),
    (
        '                return v, True # Hata olursa yine de geçir',
        '                return v, True # Pass through on error',
    ),
    (
        '        # 10 videoyu paralel analiz et (Çok hızlıdır, Groq <1sn\'de döner)',
        '        # Analyse 10 videos in parallel (very fast, Groq returns in <1s)',
    ),
    (
        '        # Eğer yapay zeka 3 tane bile uyumlu bulamadıysa, eldekileri doldur (Fallback)',
        '        # If AI cannot find even 3 compatible videos, fill with available ones (Fallback)',
    ),
    (
        '        app_logger.info(f"[Prophet Picks] {len(top_picks)} adet öneri seçildi.")',
        '        app_logger.info(f"[Prophet Picks] {len(top_picks)} recommendations selected.")',
    ),
    (
        '        return {"error": "Prophet Picks yüklenemedi."}',
        '        return {"error": "Prophet Picks could not be loaded."}',
    ),
    (
        "            return {\"error\": \"Şu an trend olan video bulunamadı.\"}",
        '            return {"error": "No currently trending videos found."}',
    ),
    (
        '        # Tekrar eden URL\'leri kaldır (birden fazla sorguda aynı video çıkabilir)',
        "        # Remove duplicate URLs (the same video may appear in multiple queries)",
    ),
    (
        "        # Velocity'ye göre sırala (en yüksek önce)",
        "        # Sort by velocity (highest first)",
    ),
    (
        '        # En hızlı yükselen ilk 10 videoyu al',
        '        # Take the top 10 fastest-rising videos',
    ),
    (
        '        # ── Groq ile Yapay Zeka Uyumluluk Filtresi (Sadece En Hızlılara) ──',
        '        # ── AI Compatibility Filter with Groq (Only for the Fastest) ──',
    ),
    (
        "        app_logger.info(f\"[Prophet Picks] Öz-filtreleme: {v.get('title')[:50]} atlandı.\")",
        "        app_logger.info(f\"[Prophet Picks] Self-filtering: {v.get('title')[:50]} skipped.\")",
    ),

    # ── rabbit hole / niche finder ────────────────────────────────────────────
    (
        '        raise ValueError("Bu nişte video bulunamadı.")',
        '        raise ValueError("No videos found in this niche.")',
    ),
    (
        '        raise ValueError("Geçerli veri bulunamadı.")',
        '        raise ValueError("No valid data found.")',
    ),
    (
        '    return "Analiz yapılamadı."',
        '    return "Analysis could not be performed."',
    ),
    (
        '            return {"error": "Bu nişte aykırı bir trend bulunamadı."}',
        '            return {"error": "No outlier trend found in this niche."}',
    ),
    (
        '        app_logger.error(f"Rabbit Hole Hatası: {e}", exc_info=True)',
        '        app_logger.error(f"Rabbit Hole Error: {e}", exc_info=True)',
    ),
    (
        '        return {"error": "Bu nişte aykırı bir trend bulunamadı veya ağ hatası oluştu."}',
        '        return {"error": "No outlier trend found in this niche or a network error occurred."}',
    ),

    # ── clone_video endpoint ──────────────────────────────────────────────────
    (
        '    title    = payload.title.strip() or "Başlık Yok"',
        '    title    = payload.title.strip() or "No Title"',
    ),
    (
        '    title    = payload.title.strip() or "Başlık Yok"\n    channel  = payload.channel.strip() or "Bilinmeyen Kanal"',
        '    title    = payload.title.strip() or "No Title"\n    channel  = payload.channel.strip() or "Unknown Channel"',
    ),
    (
        '    app_logger.warning(f"[clone_video] Transcript çağrısında hata (Fallback kullanılacak): {e}")',
        '    app_logger.warning(f"[clone_video] Transcript call error (using Fallback): {e}")',
    ),
    (
        '    app_logger.warning(f"[clone_video] Transcript alınamadı (Fallback kullanılacak): {transcript}")',
        '    app_logger.warning(f"[clone_video] Transcript unavailable (using Fallback): {transcript}")',
    ),
    (
        '    # ── 2. Groq API anahtarı ─────────────────────────────────',
        '    # ── 2. Groq API key ──────────────────────────────────────',
    ),
    (
        '    # ── 3. AI Konsept Üretimi ────────────────────────────────',
        '    # ── 3. AI Concept Generation ─────────────────────────────',
    ),
    (
        '    app_logger.warning(f"[clone_video] Groq hatası: {e}")',
        '    app_logger.warning(f"[clone_video] Groq error: {e}")',
    ),
    (
        '    app_logger.error(f"[clone_video] AI hatası: {e}", exc_info=True)',
        '    app_logger.error(f"[clone_video] AI error: {e}", exc_info=True)',
    ),
    (
        '        raise HTTPException(status_code=500, detail=f"AI konsept üretimi başarısız: {e}")',
        '        raise HTTPException(status_code=500, detail=f"AI concept generation failed: {e}")',
    ),
    (
        '    app_logger.info(f"[clone_video] ✅ Konsept üretildi: video_id={video_id}")',
        '    app_logger.info(f"[clone_video] ✅ Concept generated: video_id={video_id}")',
    ),

    # ── Groq API errors (ValueError raises) ──────────────────────────────────
    (
        '        raise ValueError("Groq API anahtarı geçersiz. Ayarlar panelinden kontrol edin.")',
        '        raise ValueError("Groq API key is invalid. Please check from the Settings panel.")',
    ),
    (
        '        raise ValueError("Groq API kotası doldu. Lütfen bir süre bekleyin.")',
        '        raise ValueError("Groq API quota is exhausted. Please wait a moment.")',
    ),
    (
        '        raise ValueError(f"Groq API hatası: HTTP {resp.status_code}")',
        '        raise ValueError(f"Groq API error: HTTP {resp.status_code}")',
    ),

    # ── clone_debate endpoint shared strings ──────────────────────────────────
    (
        '    if not transcript or transcript.startswith("HATA:"):\n        transcript = ""',
        '    if not transcript or transcript.startswith("ERROR:"):\n        transcript = ""',
    ),
    (
        '        raise HTTPException(status_code=400, detail="Video ID bulunamadı. Geçerli bir YouTube URL\'si gönderin.")',
        '        raise HTTPException(status_code=400, detail="Video ID not found. Please provide a valid YouTube URL.")',
    ),
    (
        '            detail="Groq API anahtarı ayarlanmamış. Uygulamanın Ayarlar panelinden ekleyin."',
        '            detail="Groq API key is not set. Please add it from the application Settings panel."',
    ),
    (
        '    app_logger.warning(f"[clone_debate] Transcript hatası (Fallback): {e}")',
        '    app_logger.warning(f"[clone_debate] Transcript error (Fallback): {e}")',
    ),
    (
        '    app_logger.info(f"[clone_debate] ✅ Tartışma tamamlandı: video_id={video_id}")',
        '    app_logger.info(f"[clone_debate] ✅ Debate completed: video_id={video_id}")',
    ),
    (
        '    app_logger.info(f"[clone_debate] ⚔️ Tartışma başlatıldı: {payload.model_dump()}")',
        '    app_logger.info(f"[clone_debate] ⚔️ Debate started: {payload.model_dump()}")',
    ),

    # ── _call_groq_debate persona labels in Fail-Fast loop ───────────────────
    (
        '    for label, resp in [("Persona A (Eleştirmen)", resp_a), ("Persona B (Büyücü)", resp_b)]:',
        '    for label, resp in [("Persona A (Critic)", resp_a), ("Persona B (Mage)", resp_b)]:',
    ),
    (
        '            raise HTTPException(status_code=502, detail="Groq API anahtarı geçersiz.")',
        '            raise HTTPException(status_code=502, detail="Groq API key is invalid.")',
    ),
    (
        '            raise HTTPException(status_code=429, detail="Groq API kotası doldu. Lütfen bekleyin.")',
        '            raise HTTPException(status_code=429, detail="Groq API quota exceeded. Please wait.")',
    ),

    # ── _call_groq_debate parse errors ───────────────────────────────────────
    (
        '            app_logger.error(f"[clone_debate] {label} JSON parse hatası — ham yanıt: {raw[:300]}")',
        '            app_logger.error(f"[clone_debate] {label} JSON parse error — raw response: {raw[:300]}")',
    ),
    (
        '                detail=f"{label} geçerli bir JSON döndürmedi. Ham yanıt: {raw[:200]}"',
        '                detail=f"{label} did not return valid JSON. Raw response: {raw[:200]}"',
    ),
    (
        '            app_logger.error(f"[clone_debate] {label} JSON decode hatası: {exc} | Ham: {raw[:300]}")',
        '            app_logger.error(f"[clone_debate] {label} JSON decode error: {exc} | Raw: {raw[:300]}")',
    ),
    (
        '                detail=f"{label} JSON ayrıştırılamadı: {exc}"',
        '                detail=f"{label} JSON could not be parsed: {exc}"',
    ),
    (
        '    idea_a = _parse_persona_json(raw_a, "Persona A (Eleştirmen)")',
        '    idea_a = _parse_persona_json(raw_a, "Persona A (Critic)")',
    ),
    (
        '    idea_b = _parse_persona_json(raw_b, "Persona B (Büyücü)")',
        '    idea_b = _parse_persona_json(raw_b, "Persona B (Mage)")',
    ),

    # ── Judge AI errors ───────────────────────────────────────────────────────
    (
        '            detail=f"Hakem AI Groq hatası: HTTP {resp_judge.status_code}"',
        '            detail=f"Judge AI Groq error: HTTP {resp_judge.status_code}"',
    ),
    (
        '        app_logger.error(f"[clone_debate] Hakem JSON parse hatası — ham: {raw_judge[:300]}")',
        '        app_logger.error(f"[clone_debate] Judge JSON parse error — raw: {raw_judge[:300]}")',
    ),
    (
        '            detail=f"Hakem AI geçerli bir JSON döndürmedi. Ham yanıt: {raw_judge[:200]}"',
        '            detail=f"Judge AI did not return valid JSON. Raw response: {raw_judge[:200]}"',
    ),
    (
        '        app_logger.error(f"[clone_debate] Hakem JSON decode hatası: {exc} | Ham: {raw_judge[:300]}")',
        '        app_logger.error(f"[clone_debate] Judge JSON decode error: {exc} | Raw: {raw_judge[:300]}")',
    ),
    (
        '            detail=f"Hakem AI JSON ayrıştırılamadı: {exc}"',
        '            detail=f"Judge AI JSON could not be parsed: {exc}"',
    ),
    (
        '        app_logger.error(f"[clone_debate] Hakem JSON eksik anahtar(lar): {missing} | Ham: {raw_judge[:300]}")',
        '        app_logger.error(f"[clone_debate] Judge JSON missing key(s): {missing} | Raw: {raw_judge[:300]}")',
    ),
    (
        '            detail=f"Hakem AI çıktısında eksik anahtar(lar): {missing}"',
        '            detail=f"Judge AI output is missing key(s): {missing}"',
    ),

    # ── admin login HTTP ──────────────────────────────────────────────────────
    (
        '            raise HTTPException(status_code=401, detail="Geçersiz kullanıcı adı veya şifre.")',
        '            raise HTTPException(status_code=401, detail="Invalid username or password.")',
    ),

    # ── Groq API key endpoint ─────────────────────────────────────────────────
    (
        '        return {"error": "Groq API anahtarı ayarlanmamış."}',
        '        return {"error": "Groq API key is not configured."}',
    ),
    (
        '        return {"error": f"Kanal verileri okunamadı: {str(e)}"}',
        '        return {"error": f"Channel data could not be read: {str(e)}"}',
    ),
    (
        '        return {"error": f"Savaş raporu oluşturulamadı: {str(e)}"}',
        '        return {"error": f"Battle report could not be generated: {str(e)}"}',
    ),

    # ── send_report ────────────────────────────────────────────────────────────
    (
        '    # Önce PDF\'i oluştur (export_pdf endpoint\'ini simüle et)',
        '    # First generate the PDF (simulating the export_pdf endpoint)',
    ),

    # ── default content_type / purpose defaults ──────────────────────────────
    (
        '    content_type = "Genel İçerik"\n    purpose = "İzleyici Eğlendirmek"',
        '    content_type = "General Content"\n    purpose = "Entertaining the Audience"',
    ),
    (
        '    content_type = "Genel İçerik"\n    purpose      = "İzleyici Eğlendirmek"',
        '    content_type = "General Content"\n    purpose      = "Entertaining the Audience"',
    ),
    (
        '            queries = [f"{content_type} trend", f"{content_type} yeni", f"{content_type} popüler"]',
        '            queries = [f"{content_type} trend", f"{content_type} new", f"{content_type} popular"]',
    ),
    (
        '        # 3 sorguyu PARALEL çalıştır (threadpool\'da, async-safe)',
        '        # Run 3 queries IN PARALLEL (in threadpool, async-safe)',
    ),
    (
        '            return_exceptions=True  # Bir sorgu hata verse diğerleri çalışmaya devam eder',
        '            return_exceptions=True  # If one query fails, others continue running',
    ),
    (
        '        # Tüm sonuçları birleştir',
        '        # Merge all results',
    ),
    (
        '                # Dinamik Öz-karşılaştırma bug fix: Kullanıcının kendi videoları atlanır',
        '                # Dynamic self-comparison bug fix: user\'s own videos are skipped',
    ),

    # ── Pydantic model field defaults (user-facing) ───────────────────────────
    (
        '    title:     str = Field(default="Başlık Yok", description="Video başlığı")',
        '    title:     str = Field(default="No Title", description="Video title")',
    ),
    (
        '    channel:   str = Field(default="Bilinmeyen Kanal", description="Kanal adı")',
        '    channel:   str = Field(default="Unknown Channel", description="Channel name")',
    ),
    (
        '    user_id:   int = Field(default=0, description="Kullanıcı ID")',
        '    user_id:   int = Field(default=0, description="User ID")',
    ),

    # ── clone_debate title/channel defaults ───────────────────────────────────
    (
        '    title    = payload.title.strip() or "Başlık Yok"\n    channel  = payload.channel.strip() or "Bilinmeyen Kanal"',
        '    title    = payload.title.strip() or "No Title"\n    channel  = payload.channel.strip() or "Unknown Channel"',
    ),

    # ── transcript fallback check ────────────────────────────────────────────
    (
        '    if not transcript or transcript.startswith("HATA:"):',
        '    if not transcript or transcript.startswith("ERROR:"):',
    ),

    # ── content_finder date parse debug ──────────────────────────────────────
    (
        '                    app_logger.debug(f"Hata [content_finder date parse]: {e}")',
        '                    app_logger.debug(f"Error [content_finder date parse]: {e}")',
    ),

    # ── INDUSTRY_STANDARDS Turkish key ───────────────────────────────────────
    (
        "    'eğitim': {'tempo': 4.5, 'seo': 9.5, 'retention': 7.0},",
        "    'education': {'tempo': 4.5, 'seo': 9.5, 'retention': 7.0},",
    ),

    # ── niche_checker ─────────────────────────────────────────────────────────
    (
        '            content_type = "Genel İçerik"\n            purpose = "İzleyici Eğlendirmek"',
        '            content_type = "General Content"\n            purpose = "Entertaining the Audience"',
    ),

    # ── resend_verification user not found ───────────────────────────────────
    (
        '                return {"error": "Kullanıcı bulunamadı."}',
        '                return {"error": "User not found."}',
    ),
]


def apply_replacements(text: str) -> tuple[str, int]:
    """Apply all replacements and return (new_text, change_count)."""
    count = 0
    for old, new in REPLACEMENTS:
        if old in text:
            text = text.replace(old, new)
            count += 1
    return text, count


def main():
    if not os.path.exists(SRC):
        print(f"❌ Source file not found: {SRC}")
        return

    # Backup
    shutil.copy2(SRC, BACKUP)
    print(f"[OK] Backup created: {BACKUP}")

    with open(SRC, "r", encoding="utf-8") as f:
        original = f.read()

    updated, n = apply_replacements(original)

    with open(SRC, "w", encoding="utf-8") as f:
        f.write(updated)

    print(f"[OK] Done -- {n} replacement(s) applied to {SRC}.")
    if n < len(REPLACEMENTS):
        print(f"   [INFO] {len(REPLACEMENTS) - n} pattern(s) were not found in the file (may have been already translated).")


if __name__ == "__main__":
    main()
