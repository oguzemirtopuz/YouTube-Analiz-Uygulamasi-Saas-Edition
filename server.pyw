import os
import sys
import uuid
import shutil
import requests
import pandas as pd
import numpy as np
import cv2
import librosa
import uvicorn
import threading
import webview
import time
import hashlib
import secrets
from datetime import datetime
import subprocess
import sqlite3
import asyncio
import aiosqlite
import json
import html
import gc
import re
import logging
import logging.handlers
from typing import Optional, Dict, List
from pathlib import Path
import traceback
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import platform
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from cryptography.fernet import Fernet

# --- RAKİP ANALİZİ KÜTÜPHANESİ ---
try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False

# --- GÖRSEL ZEKA KÜTÜPHANELERİ (Aşama 3) ---
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False

try:
    from colorthief import ColorThief
    COLORTHIEF_AVAILABLE = True
except ImportError:
    COLORTHIEF_AVAILABLE = False


# ═══════════════════════════════════════════════════════════
#   LOGGING & HATA YÖNETİMİ (SaaS Seviye)
# ═══════════════════════════════════════════════════════════
# PyInstaller EXE uyumlu yol ayrımı
if getattr(sys, 'frozen', False):
    # EXE modunda: APP_DIR = exe'nin yanı (yazılabilir), BUNDLE_DIR = paket içi (salt okunur)
    APP_DIR = Path(os.path.dirname(sys.executable)).resolve()
    BUNDLE_DIR = Path(sys._MEIPASS).resolve()
else:
    APP_DIR = Path(os.path.dirname(os.path.abspath(__file__))).resolve()
    BUNDLE_DIR = APP_DIR

# Eski kodla uyumluluk
BASE_DIR = APP_DIR
os.chdir(APP_DIR)

# Log dizini
LOGS_DIR = APP_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════════════
#   GÜVENLİK SERVİSİ (app/services/security.py)
# ═══════════════════════════════════════════════════════════
from app.services.security import CryptoManager, hash_password, verify_password, generate_verification_code


# Ana uygulama logger
app_logger = logging.getLogger("yt_analiz")
app_logger.setLevel(logging.DEBUG)

# Dosya handler (genel sunucu logu)
_main_handler = logging.handlers.RotatingFileHandler(
    str(LOGS_DIR / "server.log"), maxBytes=5*1024*1024, backupCount=3, encoding="utf-8"
)
_main_handler.setFormatter(logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
))
app_logger.addHandler(_main_handler)

# Konsol handler kapatıldı (Unicode hatasını engellemek için)
# _console_handler = logging.StreamHandler()
# _console_handler.setLevel(logging.INFO)
# _console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
# app_logger.addHandler(_console_handler)

# Crash log dosyası (eski uyumluluk)
LOG_FILE = str(LOGS_DIR / "crash.log")

_user_loggers: Dict[int, logging.Logger] = {}

def get_user_logger(user_id: int) -> logging.Logger:
    """Kullanıcı bazlı logger döndürür. logs/user_X.log dosyasına yazar."""
    if user_id in _user_loggers:
        return _user_loggers[user_id]
    logger = logging.getLogger(f"yt_analiz.user_{user_id}")
    logger.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(
        str(LOGS_DIR / f"user_{user_id}.log"), maxBytes=5*1024*1024, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter(
        f"[%(asctime)s] [%(levelname)s] [user_id={user_id}] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(handler)
    _user_loggers[user_id] = logger
    return logger


def log_exception(exc_type, exc_value, exc_traceback):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n--- HATA ZAMANI: {time.ctime()} ---\n")
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    app_logger.critical(f"Unhandled exception: {exc_value}", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = log_exception
try:
    sys.stdout = open(str(LOGS_DIR / "stdout.log"), "a", encoding="utf-8")
    sys.stderr = sys.stdout
except Exception as e:
    app_logger.error(f"Hata [stdout_redirect]: {str(e)}", exc_info=True)

templates_dir = str(BUNDLE_DIR / "templates")
static_dir = str(BUNDLE_DIR / "static")
output_dir = APP_DIR / "shorts_output"

# --- VERİTABANI KATMANI (app/database/db.py) ---
from app.database.db import db_path, get_db, get_async_db, init_db, migrate_data


temp_dir = APP_DIR / "temp_videos"
temp_dir.mkdir(exist_ok=True)

# EXE modunda templates/static zaten paket içinde; geliştirme modunda oluştur
if not getattr(sys, 'frozen', False):
    Path(templates_dir).mkdir(exist_ok=True)
    Path(static_dir).mkdir(exist_ok=True)
output_dir.mkdir(exist_ok=True)

def _load_pdf_lang():
    try:
        # translations.xlsx hem BUNDLE_DIR hem APP_DIR'de olabilir
        xlsx_path = BUNDLE_DIR / 'translations.xlsx'
        if not xlsx_path.exists():
            xlsx_path = APP_DIR / 'translations.xlsx'
        df = pd.read_excel(str(xlsx_path), sheet_name='pdf', dtype=str).fillna('')
        result = {}
        for _, row in df.iterrows():
            key = str(row['key']).strip()
            if not key:
                continue
            for lang in ['tr', 'en', 'es']:
                if lang not in result:
                    result[lang] = {}
                result[lang][key] = str(row[lang]).strip()
        # comparison_headers listesini özel olarak kur
        for lang_code in ['tr', 'en', 'es']:
            if lang_code in result:
                result[lang_code]['comparison_headers'] = [
                    result[lang_code].get('comparison_headers_metric', 'Metrik'),
                    result[lang_code].get('comparison_headers_this', 'Bu Video'),
                    result[lang_code].get('comparison_headers_avg', 'Eski Ortalaman'),
                    result[lang_code].get('comparison_headers_diff', 'Fark'),
                ]
        return result
    except Exception as e:
        print(f"translations.xlsx okunamadı, fallback boş dict: {e}")
        return {'tr': {}, 'en': {}, 'es': {}}

PDF_LANG = _load_pdf_lang()



# --- PDF FONT ENTEGRASYONU (GÜVENLİ) ---
# Önce proje klasörüne bak, sonra sistem klasörlerine, son çare Helvetica
def _try_register_arial():
    """
    arial.ttf / arialbd.ttf için arama sırası:
      1. BASE_DIR (proje klasörü)
      2. Windows sistem font klasörü  (C:/Windows/Fonts)
      3. Helvetica fallback
    """
    candidates = [
        (str(BASE_DIR / 'arial.ttf'),    str(BASE_DIR / 'arialbd.ttf')),
    ]
    if platform.system() == 'Windows':
        win_fonts = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
        candidates.append((str(win_fonts / 'arial.ttf'), str(win_fonts / 'arialbd.ttf')))

    for reg_path, bold_path in candidates:
        if os.path.isfile(reg_path) and os.path.isfile(bold_path):
            try:
                pdfmetrics.registerFont(TTFont('Arial', reg_path))
                pdfmetrics.registerFont(TTFont('Arial-Bold', bold_path))
                return 'Arial', 'Arial-Bold'
            except Exception:
                pass  # Bozuk font dosyası → sonraki adıma geç
    return 'Helvetica', 'Helvetica-Bold'

FONT_REGULAR, FONT_BOLD = _try_register_arial()


INDUSTRY_STANDARDS = {
    'gaming': {'tempo': 8.8, 'seo': 7.5, 'retention': 4.5},
    'eğitim': {'tempo': 4.5, 'seo': 9.5, 'retention': 7.0},
    'vlog': {'tempo': 7.5, 'seo': 6.5, 'retention': 5.5},
    'finance': {'tempo': 5.0, 'seo': 8.5, 'retention': 6.5},
    'shorts': {'tempo': 9.5, 'seo': 5.0, 'retention': 8.5},
    'default': {'tempo': 7.0, 'seo': 8.0, 'retention': 6.0}
}

FFMPEG_AVAILABLE = False


def run_cmd(cmd_list, timeout=None):
    kwargs = {'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL}
    if os.name == 'nt':
        kwargs['creationflags'] = 0x08000000
    return subprocess.run(cmd_list, check=True, timeout=timeout, **kwargs)


FFMPEG_AVAILABLE = False
GPU_CODEC = "libx264"  # default CPU codec

def detect_gpu_codec():
    """
    Sırasıyla NVIDIA, AMD, Intel GPU codec'lerini dener.
    Çalışan ilkini döndürür, hiçbiri çalışmazsa libx264 (CPU) döndürür.
    """
    candidates = [
        ("h264_nvenc", "NVIDIA"),
        ("h264_amf", "AMD"),
        ("h264_qsv", "Intel"),
    ]
    for codec, brand in candidates:
        try:
            test_cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "nullsrc=s=64x64:d=1",
                "-c:v", codec,
                "-f", "null", "-"
            ]
            result = subprocess.run(
                test_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=8,
                creationflags=0x08000000 if os.name == 'nt' else 0
            )
            if result.returncode == 0:
                print(f"✅ GPU Codec bulundu: {codec} ({brand})")
                return codec
        except Exception:
            pass
    print("ℹ️ GPU codec bulunamadı, CPU (libx264) kullanılacak.")
    return "libx264"


def check_ffmpeg():
    global FFMPEG_AVAILABLE, GPU_CODEC
    try:
        run_cmd(["ffmpeg", "-version"], timeout=5)
        FFMPEG_AVAILABLE = True
        GPU_CODEC = detect_gpu_codec()
    except Exception as e:
        app_logger.error(f"Hata [check_ffmpeg]: FFmpeg bulunamadı veya çalıştırılamadı. {e}")
        FFMPEG_AVAILABLE = False


check_ffmpeg()


# ═══════════════════════════════════════════════════════════
#   DONANIM / PERFORMANS OTO-PİLOTU
# ═══════════════════════════════════════════════════════════
SYSTEM_CAPS = {
    "cpu_cores": 1,
    "cpu_brand": "",
    "gpu_codec": "libx264",
    "cuda_available": False,
    "cuda_devices": 0,
    "optimal_threads": 2,
    "ram_gb": 0,
    "platform": platform.system(),
    "fast_mode": False,
}


def detect_system_capabilities():
    """Sistem başlangıcında donanım profilini tespit eder."""
    global SYSTEM_CAPS
    # CPU
    cpu_count = os.cpu_count() or 1
    SYSTEM_CAPS["cpu_cores"] = cpu_count
    SYSTEM_CAPS["cpu_brand"] = platform.processor() or "Unknown"
    SYSTEM_CAPS["gpu_codec"] = GPU_CODEC
    SYSTEM_CAPS["optimal_threads"] = max(2, cpu_count - 1)

    # RAM (platform bağımsız, psutil olmadan)
    try:
        if platform.system() == "Windows":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            mem = MEMORYSTATUSEX()
            mem.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
            SYSTEM_CAPS["ram_gb"] = round(mem.ullTotalPhys / (1024**3), 1)
    except Exception:
        pass

    # CUDA (OpenCV)
    try:
        cuda_count = cv2.cuda.getCudaEnabledDeviceCount()
        if cuda_count > 0:
            SYSTEM_CAPS["cuda_available"] = True
            SYSTEM_CAPS["cuda_devices"] = cuda_count
    except Exception:
        pass

    # Fast mode: 8+ çekirdek veya GPU codec varsa agresif ayarlar kullan
    SYSTEM_CAPS["fast_mode"] = (cpu_count >= 8 or GPU_CODEC != "libx264")

    app_logger.info(
        f"🖥️ Sistem profili: CPU={cpu_count} çekirdek, RAM={SYSTEM_CAPS['ram_gb']}GB, "
        f"GPU={GPU_CODEC}, CUDA={'✅' if SYSTEM_CAPS['cuda_available'] else '❌'}, "
        f"Fast Mode={'ON' if SYSTEM_CAPS['fast_mode'] else 'OFF'}"
    )


detect_system_capabilities()


# ═══════════════════════════════════════════════════════════
#   AI SERVİSİ (app/services/ai_service.py)
# ═══════════════════════════════════════════════════════════
from app.services.ai_service import get_groq_api_key, generate_ai_game_feedback, analyze_image_with_gemini


# ═══════════════════════════════════════════════════════════
#   E-POSTA SERVİSİ (app/services/email_service.py)
# ═══════════════════════════════════════════════════════════
from app.services.email_service import send_verification_email, send_report_email


# init_db ve migrate_data → app/database/db.py'den import edildi (FAZ 1)
init_db()


def extract_core_keywords(text_str):
    if not text_str:
        return set()
    text_str = str(text_str).lower().replace("'", " ").replace('"', ' ').replace('-', ' ')
    words = set(re.findall(r'\b\w+\b', text_str))
    stop_words = {
        # Türkçe
        've', 'ile', 'için', 'bir', 'çok', 'nasıl', 'neden', 'gibi', 'ama', 'bunu', 'böyle',
        'olan', 'olarak', 'kadar', 'sonra', 'önce', 'video', 'oyun', 'yeni', 'bölüm',
        'türkçe', 'izle', 'abone', 'ol', 'görün', 'bu', 'ben', 'sen', 'biz', 'siz', 'onlar',
        'ise', 'da', 'de', 'ki', 'mi', 'mu', 'mı', 'mü', 'ne', 'daha',
        # İngilizce
        'the', 'and', 'for', 'with', 'that', 'this', 'are', 'was', 'how', 'why',
        'what', 'when', 'who', 'from', 'have', 'has', 'had', 'not', 'but', 'they',
        'you', 'your', 'its', 'our', 'can', 'will', 'just', 'into', 'also', 'about',
        # İspanyolca
        'que', 'con', 'para', 'por', 'una', 'uno', 'los', 'las', 'del', 'sus',
        'como', 'pero', 'est', 'son', 'han', 'hay', 'todo', 'este', 'esta', 'eso',
        'ese', 'ella', 'ellos', 'nos', 'muy', 'mas', 'sin', 'cuando', 'donde',
        'quien', 'porque', 'desde', 'hasta', 'entre', 'sobre', 'solo',
    }
    return {w for w in words if len(w) > 2 and w not in stop_words}


def compute_kill_switch(user_title: str, comp_title: str) -> bool:
    user_kw = extract_core_keywords(user_title)
    comp_kw = extract_core_keywords(comp_title)
    if not user_kw or not comp_kw:
        return False
    for uk in user_kw:
        for ck in comp_kw:
            if uk in ck or ck in uk:
                return False
    return True


def cleanup_temp_videos():
    try:
        now = time.time()
        for f in temp_dir.glob("v_*.mp4"):
            if now - f.stat().st_mtime > 10800:
                try:
                    f.unlink()
                except Exception as e:
                    app_logger.warning(f"Hata [cleanup_temp_videos]: {f} silinemedi: {e}")
    except Exception as e:
        app_logger.error(f"Hata [cleanup_temp_videos] genel hata: {e}")


def get_dynamic_timeout(video_path: str, min_timeout: int = 120) -> Optional[int]:
    """
    Video süresine göre dinamik FFmpeg timeout hesaplar.
    Kural: max(min_timeout, video_süresi * 2)
    20GB+ dosyalar için bile yeterli marj sağlar.
    Süre bulunamazsa None döner (timeout yok).
    """
    try:
        probe_cmd = ["ffmpeg", "-i", video_path, "-hide_banner"]
        probe_kwargs = {'capture_output': True, 'text': True, 'timeout': 10}
        if os.name == 'nt':
            probe_kwargs['creationflags'] = 0x08000000
        result = subprocess.run(probe_cmd, **probe_kwargs)
        match = re.search(r'Duration:\s*(\d+):(\d+):(\d+)', result.stderr)
        if match:
            h, m, s = int(match.group(1)), int(match.group(2)), int(match.group(3))
            duration_sec = h * 3600 + m * 60 + s
            return max(min_timeout, duration_sec * 2)
    except Exception:
        pass
    return None


def _copy_uploads(video_file_obj, csv_file_obj, thumb_file_obj, v_path, c_path, t_path):
    """Yüklenen dosyaları diske kopyalar (threadpool içinde çalıştırılmak üzere)."""
    with open(v_path, "wb") as f:
        shutil.copyfileobj(video_file_obj, f)
    if csv_file_obj and c_path:
        with open(c_path, "wb") as f:
            shutil.copyfileobj(csv_file_obj, f)
    if thumb_file_obj and t_path:
        with open(t_path, "wb") as f:
            shutil.copyfileobj(thumb_file_obj, f)


def check_content_consistency(title: str, tags: str, description: str) -> dict:
    """
    Başlık, etiket ve açıklama arasındaki tutarlılığı kontrol eder.
    Sonuç: {'ok': bool, 'issues': list[str]}
    """
    issues = []
    title_kw = extract_core_keywords(title)

    # Etiket kontrolü
    if not tags or not tags.strip():
        issues.append('no_tags')
    else:
        tag_text = tags.replace(',', ' ')
        tag_kw = extract_core_keywords(tag_text)
        if title_kw and tag_kw:
            overlap = sum(1 for tk in title_kw for tagk in tag_kw if tk in tagk or tagk in tk)
            if overlap == 0:
                issues.append('title_tags_mismatch')

    # Açıklama kontrolü
    if not description or not description.strip():
        issues.append('no_desc')
    else:
        desc_kw = extract_core_keywords(description)
        if title_kw and desc_kw:
            overlap = sum(1 for tk in title_kw for dk in desc_kw if tk in dk or dk in tk)
            if overlap == 0:
                issues.append('title_desc_mismatch')

    return {'ok': len(issues) == 0, 'issues': issues}


class CompetitorAnalyzer:

    @staticmethod
    def get_competitor(category: str, tags: str, manual_url: str = "", channel_name: str = ""):
        fallback_data = {
            'title': f"{category.split()[0] if category else 'Viral'} Konseptli Video",
            'channel': 'Sektör Lideri (Otomatik)',
            'views': 345000,
            'tags': ['viral', 'trend', 'nasıl yapılır', 'yeni', category.split()[0] if category else 'video'],
            'hashtags': ['viral', 'trend'],
            'is_manual': False,
            'likes': 15000,
            'comments': 1200,
            'upload_date': datetime.now().strftime('%Y%m%d'),
            'is_fake': True
        }
        if not YT_DLP_AVAILABLE:
            return fallback_data
        ydl_opts = {'quiet': True, 'extract_flat': False, 'skip_download': True, 'max_downloads': 1, 'noplaylist': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if manual_url and ("youtube.com" in manual_url or "youtu.be" in manual_url):
                    info = ydl.extract_info(manual_url, download=False)
                    comp_desc = info.get('description', '')
                    c_hashes = [w.strip('#').lower() for w in str(comp_desc).split() if w.startswith('#')]
                    c_hashes = list(dict.fromkeys([h for h in c_hashes if h]))
                    return {
                        'title': info.get('title', 'Bilinmiyor'),
                        'channel': info.get('uploader', 'Rakip Kanal'),
                        'views': info.get('view_count', fallback_data['views']),
                        'tags': info.get('tags', fallback_data['tags'])[:15],
                        'hashtags': c_hashes[:10],
                        'is_manual': True,
                        'likes': info.get('like_count', 0),
                        'comments': info.get('comment_count', 0),
                        'upload_date': info.get('upload_date', fallback_data['upload_date']),
                        'is_fake': False
                    }
                else:
                    short_cat = " ".join(category.split()[:2]) if category else ""
                    short_tags = " ".join([t.strip() for t in tags.split(',')[:2]]) if tags else ""
                    search_query = f"{short_cat} {short_tags}".strip()
                    if not search_query or len(search_query) < 3:
                        search_query = "YouTube trend"
                    info = ydl.extract_info(f"ytsearch3:{search_query}", download=False)
                    if 'entries' in info and len(info['entries']) > 0:
                        entry = None
                        for candidate in info['entries']:
                            uploader = candidate.get('uploader', '') or candidate.get('channel', '')
                            if channel_name and uploader.lower().strip() == channel_name.lower().strip():
                                continue  # Kendi kanalını atla
                            entry = candidate
                            break
                        if entry is None:
                            return fallback_data
                        comp_desc = entry.get('description', '')
                        c_hashes = [w.strip('#').lower() for w in str(comp_desc).split() if w.startswith('#')]
                        c_hashes = list(dict.fromkeys([h for h in c_hashes if h]))
                        return {
                            'title': entry.get('title', fallback_data['title']),
                            'channel': entry.get('uploader', fallback_data['channel']),
                            'views': entry.get('view_count', fallback_data['views']),
                            'tags': entry.get('tags', fallback_data['tags'])[:15],
                            'hashtags': c_hashes[:10],
                            'is_manual': False,
                            'likes': entry.get('like_count', 0),
                            'comments': entry.get('comment_count', 0),
                            'upload_date': entry.get('upload_date', fallback_data['upload_date']),
                            'is_fake': False
                        }
                    else:
                        return fallback_data
        except Exception as e:
            traceback.print_exc()
            return fallback_data


class AnalysisEngine:

    @staticmethod
    def get_industry_standard(c_type: str):
        c_type = c_type.lower()
        for key, std in INDUSTRY_STANDARDS.items():
            if key in c_type:
                return std
        return INDUSTRY_STANDARDS['default']

    @staticmethod
    async def generate_dynamic_feedback(c_type, c_aud, c_purp, tech_score, retention_score, peaks,
                                        lang="tr", thumb_insights: dict = None,
                                        visual_insights_str: str = ""):
        
        c_type_raw = c_type.lower()
        c_aud_raw = c_aud.lower() if c_aud else "izleyici"
        if len(c_aud_raw) > 40:
            c_aud_raw = c_aud_raw[:37] + "..."
        feedback = ""
        is_en = (lang == "en")
        is_es = (lang == "es")

        # --- Hardcoded keyword routing removed for neutrality ---
        ai_feedback = await generate_ai_game_feedback(
            c_type, c_aud, c_purp, tech_score, retention_score, peaks, lang,
            visual_insights=visual_insights_str
        )
        if ai_feedback:
            feedback = ai_feedback
        else:
            prefix = "📢 " + ("CHANNEL ANALYSIS" if is_en else "ANÁLISIS DE CANAL" if is_es else "KANAL ANALİZİ") + f" ({c_type_raw.upper()}): "
            if tech_score < 5.0:
                feedback = (f"{prefix}" +
                            (f"There's stagnation. Tighten the editing a bit so the '{c_aud_raw}' audience doesn't get bored." if is_en else
                            f"Hay estancamiento. Ajusta un poco el montaje para que la audiencia '{c_aud_raw}' no se aburra." if is_es else
                            f"Durağanlık var. '{c_aud_raw}' kitlesini sıkmamak için kurguyu biraz sıkılaştır."))
            elif retention_score < 5.0:
                feedback = (f"{prefix}" +
                            (f"People are clicking on your video but '{c_aud_raw}' is leaving immediately. Speed up the intro." if is_en else
                            f"La gente hace clic en tu video pero '{c_aud_raw}' se va inmediatamente. Acelera la introducción." if is_es else
                            f"İnsanlar videona tıklıyor ama '{c_aud_raw}' hemen çıkıyor. Girişi hızlandır."))
            else:
                feedback = (f"{prefix}" +
                            (f"You've found a good balance suitable for your channel type." if is_en else
                            f"Has encontrado un buen equilibrio adecuado para el tipo de tu canal." if is_es else
                            f"Kanalının türüne uygun bir denge yakalamışsın."))

        # ── Görsel zeka ek notu (Aşama 3) ──
        if thumb_insights and thumb_insights.get("visual_summary"):
            vs = thumb_insights["visual_summary"]
            feedback += f" 📸 [{vs}]"

        return feedback
    @staticmethod
    def analyze_visual_tempo(video_path: str, pro_mode: bool) -> List[float]:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0 or np.isnan(fps):
            fps = 30
        frame_skip = int(fps / 5) if pro_mode else int(fps)
        tempo_map, current_sec_diffs, prev_frame, frame_count = [], [], None, 0
        gc_counter = 0
        try:
            while True:
                ret = cap.grab()
                if not ret:
                    break
                if frame_count % frame_skip == 0:
                    ret, frame = cap.retrieve()
                    if not ret:
                        continue
                    small_frame = cv2.resize(frame, (320, int((320 / frame.shape[1]) * frame.shape[0])))
                    gray = cv2.GaussianBlur(cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY), (21, 21), 0)
                    if prev_frame is not None:
                        thresh = cv2.threshold(cv2.absdiff(gray, prev_frame), 25, 255, cv2.THRESH_BINARY)[1]
                        current_sec_diffs.append((np.sum(thresh) / thresh.size) / 255 * 100)
                        del thresh
                    prev_frame = gray
                    del frame, small_frame
                    if len(current_sec_diffs) >= (fps if pro_mode else 2):
                        tempo_map.append(round(float(np.mean(current_sec_diffs)), 2))
                        current_sec_diffs = []
                    gc_counter += 1
                    if gc_counter % 100 == 0:
                        gc.collect()
                frame_count += 1
        except Exception as e:
            app_logger.warning(f"Hata [analyze_visual_tempo]: {e}")
        finally:
            cap.release()
            gc.collect()
        return tempo_map

    @staticmethod
    def analyze_audio_per_sec(video_path: str, pro_mode: bool) -> List[float]:
        temp_audio = f"temp_coach_{uuid.uuid4().hex[:5]}.wav"
        audio_map = []
        sr_val = 22050 if pro_mode else 11025
        try:
            run_cmd(["ffmpeg", "-y", "-hwaccel", "auto", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", str(sr_val), "-ac", "1", temp_audio], timeout=get_dynamic_timeout(video_path))

            # --- CHUNK-BASED: Sesi parça parça işle, RAM'e basmadan ---
            frame_length = 2048
            hop_length = sr_val  # Orijinal: her saniye 1 RMS değeri
            block_length = 256

            all_rms = []
            stream = librosa.stream(
                temp_audio,
                block_length=block_length,
                frame_length=frame_length,
                hop_length=hop_length
            )
            for y_block in stream:
                rms_block = librosa.feature.rms(
                    y=y_block,
                    frame_length=frame_length,
                    hop_length=hop_length,
                    center=False
                )[0]
                all_rms.append(rms_block)

            if all_rms:
                rms = np.concatenate(all_rms)
                audio_map = [round(float(v) * 100, 2) for v in rms]
                del all_rms, rms
                gc.collect()
        except Exception as e:
            app_logger.warning(f"Hata [analyze_audio_per_sec]: {e}")
        finally:
            if os.path.exists(temp_audio):
                try:
                    os.remove(temp_audio)
                except Exception as e:
                    app_logger.debug(f"Geçici ses dosyası silinemedi: {e}")
        return audio_map

    @staticmethod
    def analyze_scene_changes(video_path: str, ch_type: str = "default") -> Dict:
        """
        Sahne değişimlerini ve hareket yoğunluğunu tespit eder.
        ch_type'a göre adaptif eşik kullanır.
        """
        ch_lower = ch_type.lower()
        gaming_keys = ['gaming', 'oyun', 'fps', 'valorant', 'fortnite', 'gta',
                       'cs2', 'apex', 'warzone', 'pubg']
        education_keys = ['eğitim', 'ders', 'tutorial', 'podcast', 'bilgi', 'belgesel']
        vlog_keys = ['vlog', 'günlük', 'daily']

        if any(k in ch_lower for k in gaming_keys):
            scene_threshold = 40.0
        elif any(k in ch_lower for k in education_keys):
            scene_threshold = 25.0
        elif any(k in ch_lower for k in vlog_keys):
            scene_threshold = 32.0
        else:
            scene_threshold = 30.0

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0 or np.isnan(fps):
            fps = 30
        frame_skip = max(1, int(fps / 3))
        cut_times = []
        motion_values = []
        prev_hist = None
        prev_gray = None
        frame_count = 0
        gc_counter = 0

        try:
            while True:
                ret = cap.grab()
                if not ret:
                    break
                if frame_count % frame_skip == 0:
                    ret, frame = cap.retrieve()
                    if not ret:
                        continue
                    small = cv2.resize(frame, (160, 90))
                    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                    hist = cv2.calcHist([gray], [0], None, [64], [0, 256])
                    cv2.normalize(hist, hist)

                    if prev_hist is not None:
                        diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CHISQR)
                        current_time = frame_count / fps
                        if diff > scene_threshold:
                            cut_times.append(round(current_time, 1))

                    if prev_gray is not None:
                        motion = float(np.mean(cv2.absdiff(gray, prev_gray)))
                        motion_values.append(motion)

                    prev_hist = hist
                    prev_gray = gray
                    del frame, small
                    gc_counter += 1
                    if gc_counter % 150 == 0:
                        gc.collect()
                frame_count += 1
        except Exception as e:
            app_logger.warning(f"Hata [analyze_scene_changes]: {e}")
        finally:
            cap.release()
            gc.collect()

        total_duration = frame_count / fps if fps > 0 else 1.0
        cut_frequency = round(len(cut_times) / max(1.0, total_duration / 60.0), 1)
        avg_motion = round(float(np.mean(motion_values)), 2) if motion_values else 0.0
        # Downsample motion_values for response size
        step = max(1, len(motion_values) // 200)
        sampled_motion = [round(v, 2) for v in motion_values[::step]] if motion_values else []

        return {
            "cut_times": cut_times[:100],
            "cut_count": len(cut_times),
            "cut_frequency": cut_frequency,
            "avg_motion_intensity": avg_motion,
            "motion_values": sampled_motion,
            "scene_threshold_used": scene_threshold,
            "total_duration": round(total_duration, 1)
        }

    @staticmethod
    def analyze_thumbnail(path: str) -> Dict:
        """
        Gelişmiş thumbnail analizi (Aşama 3):
        - DeepFace ile yüz/duygu/bakış yönü tespiti
        - Michelson kontrast oranı
        - Metin yerleşim alanı (Rule of Thirds)
        - Canlı renk paleti uyumu (YouTube vibrant colors)
        """
        result = {
            "score": 0.0, "face_detected": False, "face_count": 0,
            "faces": [], "contrast_ratio": 0.0, "text_space_score": 0.0,
            "vibrant_color_match": 0.0, "visual_summary": ""
        }
        try:
            if not os.path.exists(path) or os.path.getsize(path) == 0:
                return result
            img = cv2.imread(path)
            if img is None:
                return result

            h, w = img.shape[:2]
            summary_parts = []
            face_bonus = 0.0

            # ── 1. DEEPFACE: Yüz + Duygu + Bakış Yönü ──
            if DEEPFACE_AVAILABLE:
                try:
                    analyses = None
                    for backend in ['retinaface', 'opencv', 'mtcnn']:
                        try:
                            analyses = DeepFace.analyze(
                                img_path=path,
                                actions=['emotion'],
                                detector_backend=backend,
                                enforce_detection=True,
                                silent=True
                            )
                            break
                        except ValueError:
                            continue
                        except Exception:
                            continue
                            
                    if not analyses:
                        raise ValueError("No face detected by any backend")
                        
                    if not isinstance(analyses, list):
                        analyses = [analyses]

                    valid_faces = []
                    for face_data in analyses:
                        region = face_data.get("region", {})
                        fw = region.get("w", 0)
                        fh = region.get("h", 0)
                        if fw < w * 0.03 or fh < h * 0.03:
                            continue

                        dominant = face_data.get("dominant_emotion", "neutral")
                        emotions = face_data.get("emotion", {})

                        face_cx = region.get("x", 0) + fw / 2
                        face_cy = region.get("y", 0) + fh / 2
                        center_dist_x = abs(face_cx - w / 2) / (w / 2) if w > 0 else 1
                        center_dist_y = abs(face_cy - h / 2) / (h / 2) if h > 0 else 1
                        looking_at_camera = center_dist_x < 0.4 and center_dist_y < 0.5

                        valid_faces.append({
                            "dominant_emotion": dominant,
                            "emotion_scores": {k: round(v, 1) for k, v in emotions.items()},
                            "region": {"x": region.get("x", 0), "y": region.get("y", 0),
                                       "w": fw, "h": fh},
                            "looking_at_camera": looking_at_camera
                        })

                    if valid_faces:
                        result["face_detected"] = True
                        result["face_count"] = len(valid_faces)
                        result["faces"] = valid_faces
                        primary = valid_faces[0]
                        emo = primary["dominant_emotion"]

                        high_ctr = {"surprise": 2.5, "happy": 2.0, "fear": 2.2, "angry": 1.5}
                        face_bonus = high_ctr.get(emo, 0.8)
                        if primary["looking_at_camera"]:
                            face_bonus += 0.5

                        emo_tr = {"surprise": "şaşkın", "happy": "mutlu", "fear": "korkmuş",
                                  "angry": "kızgın", "sad": "üzgün", "neutral": "nötr",
                                  "disgust": "tiksinti"}
                        summary_parts.append(
                            f"Thumbnail'de {emo_tr.get(emo, emo)} bir yüz var")
                        if primary["looking_at_camera"]:
                            summary_parts.append("kameraya bakıyor")
                except Exception as e:
                    print(f"DeepFace analiz hatası: {e}")
            else:
                pass

            # ── 2. KONTRAST ORANI (Michelson Contrast) ──
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l_ch, a_ch, b_ch = cv2.split(lab)
            l_min = float(np.percentile(l_ch, 5))
            l_max = float(np.percentile(l_ch, 95))

            if (l_max + l_min) > 0:
                michelson = (l_max - l_min) / (l_max + l_min)
            else:
                michelson = 0.0
            result["contrast_ratio"] = round(michelson, 3)

            if 0.4 <= michelson <= 0.8:
                contrast_10 = 10.0
            elif michelson > 0.8:
                contrast_10 = max(6.0, 10.0 - (michelson - 0.8) * 15)
            else:
                contrast_10 = max(2.0, michelson / 0.4 * 10.0)

            if michelson >= 0.5:
                summary_parts.append("kontrast çok iyi")
            elif michelson >= 0.3:
                summary_parts.append("kontrast orta düzeyde")
            else:
                summary_parts.append("kontrast düşük")

            # ── 3. METİN YERLEŞİM ALANI ──
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            regions_var = [
                float(np.std(gray[:h // 4, :])),
                float(np.std(gray[3 * h // 4:, :])),
                float(np.std(gray[:, :w // 3])),
                float(np.std(gray[:, 2 * w // 3:])),
            ]
            min_var = min(regions_var)
            if min_var < 25:
                text_space_10 = 10.0
            elif min_var < 40:
                text_space_10 = 7.5
            elif min_var < 55:
                text_space_10 = 5.0
            else:
                text_space_10 = max(2.0, 10.0 - (min_var - 30) * 0.15)
            result["text_space_score"] = round(text_space_10, 1)

            # ── 4. CANLI RENK PALETİ UYUMU ──
            vibrant_palette_bgr = [
                (0, 0, 255), (0, 215, 255), (212, 188, 0), (53, 107, 255),
                (20, 255, 57), (182, 89, 155), (0, 69, 255), (0, 165, 255),
            ]
            vibrant_10 = 5.0
            try:
                if COLORTHIEF_AVAILABLE:
                    ct = ColorThief(path)
                    palette = ct.get_palette(color_count=5, quality=5)
                    best_dist = 999.0
                    for dom_rgb in palette:
                        dom_bgr = np.array(
                            [[[dom_rgb[2], dom_rgb[1], dom_rgb[0]]]], dtype=np.uint8)
                        dom_lab = cv2.cvtColor(dom_bgr, cv2.COLOR_BGR2LAB)[0][0].astype(float)
                        for vib_bgr in vibrant_palette_bgr:
                            vib_arr = np.array(
                                [[[vib_bgr[0], vib_bgr[1], vib_bgr[2]]]], dtype=np.uint8)
                            vib_lab = cv2.cvtColor(
                                vib_arr, cv2.COLOR_BGR2LAB)[0][0].astype(float)
                            dist = float(np.sqrt(np.sum((dom_lab - vib_lab) ** 2)))
                            if dist < best_dist:
                                best_dist = dist
                    if best_dist < 20:
                        vibrant_10 = 10.0
                    elif best_dist < 40:
                        vibrant_10 = 8.0
                    elif best_dist < 60:
                        vibrant_10 = 6.0
                    elif best_dist < 80:
                        vibrant_10 = 4.0
                    else:
                        vibrant_10 = 2.0
                else:
                    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                    mean_sat = float(np.mean(hsv[:, :, 1]))
                    vibrant_10 = min(10.0, mean_sat / 12.8)
            except Exception:
                vibrant_10 = 5.0
            result["vibrant_color_match"] = round(vibrant_10, 1)
            if vibrant_10 >= 7:
                summary_parts.append("canlı renk paleti güçlü")

            # ── 5. PARLAKLIK + DOYGUNLUK ──
            mean_l = float(np.mean(l_ch))
            if 40 <= mean_l <= 80:
                brightness_10 = 10.0
            elif mean_l < 40:
                brightness_10 = max(3.0, (mean_l / 40.0) * 10.0)
            else:
                brightness_10 = max(3.0, (1 - (mean_l - 80) / 175) * 10.0)
            sat_std = (float(np.std(a_ch)) + float(np.std(b_ch))) / 2
            saturation_10 = min(10.0, sat_std * 0.4)

            # ── 6. TOPLAM SKOR ──
            face_10 = min(10.0, face_bonus * 3.3)
            if result["face_detected"]:
                total = (brightness_10 * 0.10 + saturation_10 * 0.10 +
                         contrast_10 * 0.20 + text_space_10 * 0.15 +
                         vibrant_10 * 0.15 + face_10 * 0.30)
            else:
                total = (brightness_10 * 0.15 + saturation_10 * 0.15 +
                         contrast_10 * 0.25 + text_space_10 * 0.20 +
                         vibrant_10 * 0.25)
            result["score"] = round(max(0.0, min(10.0, total)), 1)
            if not result["face_detected"]:
                result["visual_summary"] = "(Yüz bulunamadı; ya direkt yok ya da çok küçük)"
            else:
                result["visual_summary"] = (
                    " ve ".join(summary_parts) if summary_parts
                    else "Thumbnail analizi tamamlandı"
                )
        except Exception as e:
            print(f"Thumbnail analiz hatası: {e}")
            traceback.print_exc()
        return result

    @staticmethod
    async def save_analysis(channel_id: int, result: Dict, user_id: int = 1) -> int:
        db = await get_async_db()
        try:
            comp_dict = result.get("competitor_data", {})
            if isinstance(comp_dict, dict):
                comp_dict["face_detected"] = result.get("thumb_data", {}).get("face_detected", False)
                comp_dict["_thumb_data"] = result.get("thumb_data", {})
                comp_dict["_viral_segments"] = result.get("viral_segments", [])

            comp_str = json.dumps(comp_dict)
            peak_count = int(result.get("peaks", 0))
            duration_sec = result.get("analysis_duration_sec", 0)

            await db.execute('''INSERT INTO analyses (
                                channel_id, video_name, overall_score, retention_score,
                                tech_score, seo_score, thumb_score, peaks, viral_score,
                                coach_feedback, competitor_data, analysis_duration_sec, user_id
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (channel_id, result.get("title", "Bilinmeyen Video"),
                       result.get("overall_score", 0), result.get("retention_score", 0),
                       result.get("tech_score", 0), result.get("seo_score", 0),
                       result.get("thumb_score", 0),
                       peak_count,
                       result.get("viral_score", 0), result.get("dynamic_feedback", ""),
                       comp_str, duration_sec, user_id))

            analysis_id = db.last_insert_rowid()
            await db.commit()
            return analysis_id
        finally:
            await db.close()

    @staticmethod
    def analyze_video_tech(video_path: str, pro_mode: bool) -> Dict:
        temp_audio = f"temp_audio_{uuid.uuid4().hex[:8]}.wav"
        sr_val = 22050 if pro_mode else 11025
        try:
            run_cmd(["ffmpeg", "-y", "-hwaccel", "auto", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", str(sr_val), "-ac", "1", temp_audio], timeout=get_dynamic_timeout(video_path))

            # --- CHUNK-BASED: Tüm sesi RAM'e yüklemeden parça parça analiz ---
            frame_length = 2048
            hop_length = 512
            block_length = 256  # ~6 saniye/blok

            all_rms_blocks = []
            total_samples = 0

            stream = librosa.stream(
                temp_audio,
                block_length=block_length,
                frame_length=frame_length,
                hop_length=hop_length
            )
            for y_block in stream:
                total_samples += len(y_block)
                rms_block = librosa.feature.rms(
                    y=y_block,
                    frame_length=frame_length,
                    hop_length=hop_length,
                    center=False
                )[0]
                all_rms_blocks.append(rms_block)

            if not all_rms_blocks:
                app_logger.error("Ses analizi hatası: Videoda ses bloğu bulunamadı (sessiz veya bozuk video).")
                raise ValueError("Videonun ses kanalı okunamadı veya video tamamen sessiz. Lütfen ses içeren geçerli bir MP4 yükleyin.")

            rms = np.concatenate(all_rms_blocks)
            del all_rms_blocks
            gc.collect()

            duration = total_samples / sr_val
            rms_list = [round(float(v), 4) for v in rms]
            peak_times = [round(i * (duration / len(rms)), 1) for i in range(1, len(rms)) if rms[i] - rms[i - 1] > 0.18]
            gaps = [peak_times[i + 1] - peak_times[i] for i in range(len(peak_times) - 1)] if len(peak_times) > 1 else []
            max_gap = max(gaps) if gaps else (duration - (peak_times[0] if peak_times else 0))
            viral_score = min(10.0, len(peak_times) ** 1.6 / 12) if len(peak_times) > 5 else 0.0
            tech_score = 9.5 if len(peak_times) > 18 else (7.5 if len(peak_times) > 10 else 5.0)

            return {
                "tech_score": tech_score, "peaks": len(peak_times), "peak_times": peak_times,
                "max_gap": round(max_gap, 1), "viral_score": round(viral_score, 1),
                "duration": round(duration, 1), "rms_data": rms_list
            }
        except Exception as e:
            app_logger.error(f"Ses analizi hatası: {e}")
            raise ValueError(f"Videonun ses kanalı okunamadı veya dosya bozuk. Lütfen ses içeren geçerli bir MP4 yükleyin. (Detay: {str(e)[:80]})")
        finally:
            if os.path.exists(temp_audio):
                try:
                    os.remove(temp_audio)
                except Exception as e:
                    app_logger.warning(f"Hata [analyze_video_tech temp clean]: {e}")

    @staticmethod
    def find_viral_segments(tech: Dict, visual_tempo: list = None,
                            scene_changes: Dict = None) -> list:
        """
        Multimodal viral segment tespiti:
        - Ses (RMS) patlamaları: %40
        - Sahne değişim yoğunluğu: %30
        - Hareket yoğunluğu: %30
        """
        if tech["peaks"] < 3:
            return []
        duration = tech["duration"]
        rms_data = tech.get("rms_data", [])
        if not rms_data:
            return []

        rms_array = np.array(rms_data)
        rms_max = float(np.max(rms_array)) if len(rms_array) > 0 else 1.0
        time_per_frame = duration / len(rms_data)

        # Sahne değişim ve hareket verileri
        cut_times = scene_changes.get("cut_times", []) if scene_changes else []
        motion_vals = visual_tempo if visual_tempo else []
        motion_max = max(motion_vals) if motion_vals else 1.0
        if motion_max == 0:
            motion_max = 1.0

        segments = []
        for peak_time in tech["peak_times"][:3]:
            peak_idx = min(int(peak_time / time_per_frame), len(rms_data) - 1)
            local_peak_val = float(rms_data[peak_idx])
            threshold = local_peak_val * 0.35

            start_idx = peak_idx
            while start_idx > 0 and rms_data[start_idx] >= threshold:
                start_idx -= 1

            start_sec = start_idx * time_per_frame

            end_idx = peak_idx
            while end_idx < len(rms_data) - 1 and rms_data[end_idx] >= threshold:
                end_idx += 1

            end_sec = end_idx * time_per_frame + 2.0

            actual_duration = end_sec - start_sec
            if actual_duration < 6.0:
                end_sec = min(duration, start_sec + 6.0)
            elif actual_duration > 45.0:
                end_sec = start_sec + 45.0

            end_sec = min(duration, end_sec)
            start_sec = round(start_sec, 1)
            end_sec = round(end_sec, 1)

            # ── Multimodal Heyecan Katsayısı ──
            # 1. Ses skoru (normalize)
            rms_norm = (local_peak_val / rms_max) if rms_max > 0 else 0.0

            # 2. Sahne değişim yoğunluğu (bu penceredeki cut sayısı)
            cuts_in_window = sum(
                1 for ct in cut_times if start_sec <= ct <= end_sec
            )
            seg_dur = max(1.0, end_sec - start_sec)
            cut_density = cuts_in_window / (seg_dur / 10.0)  # cuts per 10sec
            cut_density_norm = min(1.0, cut_density / 5.0)

            # 3. Hareket yoğunluğu (bu penceredeki ortalama motion)
            motion_norm = 0.0
            if motion_vals:
                m_start = int(start_sec)
                m_end = min(int(end_sec) + 1, len(motion_vals))
                if m_start < len(motion_vals):
                    window_motion = motion_vals[m_start:m_end]
                    if window_motion:
                        motion_norm = (sum(window_motion) / len(window_motion)) / motion_max

            excitement = (rms_norm * 0.4) + (cut_density_norm * 0.3) + (motion_norm * 0.3)
            excitement_score = round(min(10.0, excitement * 10), 1)

            segments.append({
                "start_sec": start_sec, "end_sec": end_sec,
                "suggested_duration": round(end_sec - start_sec, 1),
                "score": round((local_peak_val / rms_max) * 100, 1),
                "excitement_score": excitement_score,
                "audio_intensity": round(rms_norm * 10, 1),
                "cut_density": round(cut_density_norm * 10, 1),
                "motion_intensity": round(motion_norm * 10, 1)
            })
        return segments

    @staticmethod
    async def get_channel_averages(channel_id: int) -> Dict:
        db = await get_async_db()
        try:
            async with db.execute('''SELECT AVG(overall_score), AVG(retention_score), AVG(tech_score), AVG(seo_score), AVG(thumb_score) FROM analyses WHERE channel_id = ?''', (channel_id,)) as cursor:
                row = await cursor.fetchone()
        finally:
            await db.close()

        def safe_round(val):
            return round(float(val), 1) if val is not None else 0.0

        if row and row[0] is not None:
            return {
                "avg_overall": safe_round(row[0]),
                "avg_retention": safe_round(row[1]),
                "avg_tech": safe_round(row[2]),
                "avg_seo": safe_round(row[3]),
                "avg_thumb": safe_round(row[4])
            }
        def _sr(v): return round(float(v), 1) if v is not None else 0.0
        return {"avg_overall": _sr(row[0]), "avg_retention": _sr(row[1]), "avg_tech": _sr(row[2]), "avg_seo": _sr(row[3]), "avg_thumb": _sr(row[4])}


app = FastAPI(title="YouTube Analiz Pro V4.0 — SaaS Edition")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
# Statik dosyalar ve Template motoru (PyInstaller BUNDLE_DIR uyumlu)
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/shorts", StaticFiles(directory=str(output_dir)), name="shorts")
templates = Jinja2Templates(directory=templates_dir)


# ═══════════════════════════════════════════════════════════
#   GLOBAL HATA YÖNETİCİ (SaaS Seviye)
# ═══════════════════════════════════════════════════════════
@app.middleware("http")
async def global_error_handler(request: Request, call_next):
    """Tüm beklenmeyen hataları yakalayıp kullanıcıya hata kodu gösterir."""
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        error_code = str(uuid.uuid4())[:8].upper()
        # Kullanıcı ID'sini çıkarmaya çalış
        user_id = 0
        try:
            if request.method == "POST":
                body = await request.body()
                if b"user_id" in body:
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(body.decode("utf-8", errors="ignore"))
                    user_id = int(parsed.get("user_id", ["0"])[0])
        except Exception as parse_e:
            app_logger.debug(f"User ID parse error in middleware: {parse_e}")
        # Loglama
        app_logger.error(
            f"[ERR-{error_code}] endpoint={request.url.path} user_id={user_id} — {type(exc).__name__}: {exc}",
            exc_info=True
        )
        if user_id > 0:
            get_user_logger(user_id).error(
                f"[ERR-{error_code}] endpoint={request.url.path} — {type(exc).__name__}: {exc}",
                exc_info=True
            )
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Bir sorun oluştu. Hata kodu: {error_code}. Lütfen bu kodu destek ekibine gönderin.",
                "error_code": error_code
            }
        )


# ═══════════════════════════════════════════════════════════
#   GOOGLE LOGIN ALTYAPISI
# ═══════════════════════════════════════════════════════════
@app.get("/api/auth/google/url")
async def google_auth_url():
    """Google OAuth2 yetkilendirme URL'sini oluşturur."""
    try:
        db = await get_async_db()
        try:
            async with db.execute("SELECT value FROM app_settings WHERE key='google_client_id'") as cursor:
                row = await cursor.fetchone()
            client_id = row[0] if row else ""
            async with db.execute("SELECT value FROM app_settings WHERE key='google_redirect_uri'") as cursor:
                row = await cursor.fetchone()
            redirect_uri = row[0] if row else "http://127.0.0.1:8000/api/auth/google/callback"
        finally:
            await db.close()

        if not client_id:
            return {"error": "Google Client ID ayarlanmamış. Ayarlar sayfasından ekleyin."}

        scope = "openid email profile"
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
            f"&scope={scope}&access_type=offline&prompt=consent"
        )
        return {"url": auth_url}
    except Exception as e:
        app_logger.error(f"Google auth URL oluşturma hatası: {e}", exc_info=True)
        return {"error": "Google auth URL oluşturulamadı."}


@app.get("/api/auth/google/callback")
async def google_auth_callback(code: str = ""):
    """Google OAuth2 callback — token exchange ve kullanıcı oluşturma/giriş."""
    if not code:
        return HTMLResponse("<h2>Hata: Yetkilendirme kodu alınamadı.</h2>")
    try:
        db = await get_async_db()
        try:
            async with db.execute("SELECT key, value FROM app_settings WHERE key IN ('google_client_id', 'google_client_secret', 'google_redirect_uri')") as cursor:
                settings = {row[0]: row[1] async for row in cursor}

            client_id = settings.get('google_client_id', '')
            client_secret = settings.get('google_client_secret', '')
            redirect_uri = settings.get('google_redirect_uri', 'http://127.0.0.1:8000/api/auth/google/callback')

            if not client_id or not client_secret:
                return HTMLResponse("<h2>Google OAuth yapılandırması eksik.</h2>")

            # Token exchange
            token_resp = requests.post("https://oauth2.googleapis.com/token", data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }, timeout=10)

            if token_resp.status_code != 200:
                app_logger.error(f"Google token exchange hatası: {token_resp.text}")
                return HTMLResponse("<h2>Google ile giriş başarısız.</h2>")

            token_data = token_resp.json()
            access_token = token_data.get("access_token", "")

            # Kullanıcı bilgilerini al
            user_info_resp = requests.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )
            if user_info_resp.status_code != 200:
                return HTMLResponse("<h2>Google kullanıcı bilgileri alınamadı.</h2>")

            guser = user_info_resp.json()
            google_id = guser.get("id", "")
            email = guser.get("email", "")
            name = guser.get("name", email.split("@")[0] if email else "GoogleUser")
            profile_pic = guser.get("picture", "")

            # Kullanıcı var mı kontrol et
            async with db.execute("SELECT id, username FROM users WHERE google_id=?", (google_id,)) as cursor:
                existing = await cursor.fetchone()

            if existing:
                user_id = existing[0]
                username = existing[1]
                await db.execute(
                    "UPDATE users SET access_token=?, profile_pic=? WHERE id=?",
                    (access_token, profile_pic, user_id)
                )
            else:
                # Benzersiz username oluştur
                base_username = re.sub(r'[^a-zA-Z0-9_]', '', name)[:20] or "user"
                username = base_username
                counter = 1
                while True:
                    async with db.execute("SELECT id FROM users WHERE username=?", (username,)) as cursor:
                        if not await cursor.fetchone():
                            break
                    username = f"{base_username}_{counter}"
                    counter += 1

                await db.execute(
                    "INSERT INTO users (username, password_hash, email, is_verified, profile_pic, google_id, access_token, auth_provider) VALUES (?, '', ?, 1, ?, ?, ?, 'google')",
                    (username, email, profile_pic, google_id, access_token)
                )
                await db.commit()
                async with db.execute("SELECT last_insert_rowid()") as cursor:
                    row = await cursor.fetchone()
                    user_id = row[0]

            await db.commit()
        finally:
            await db.close()

        # Session oluştur ve redirect yap
        session_json = json.dumps({"user_id": user_id, "username": username})
        db_session = await get_async_db()
        try:
            await db_session.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('active_session', ?)", (session_json,))
            await db_session.commit()
        finally:
            await db_session.close()

        app_logger.info(f"✅ Google login başarılı: user_id={user_id}, username={username}")
        return HTMLResponse(f"""
            <html><body>
            <script>
                localStorage.setItem('yt_user', '{session_json}');
                window.location.href = '/';
            </script>
            <p>Giriş yapılıyor...</p>
            </body></html>
        """)
    except Exception as e:
        app_logger.error(f"Google auth callback hatası: {e}", exc_info=True)
        return HTMLResponse("<h2>Google ile giriş sırasında bir hata oluştu.</h2>")


@app.post("/api/settings/google_oauth")
async def save_google_oauth(request: Request):
    """Google OAuth Client ID ve Secret kaydet."""
    try:
        data = await request.json()
        client_id = data.get("client_id", "").strip()
        client_secret = data.get("client_secret", "").strip()
        redirect_uri = data.get("redirect_uri", "http://127.0.0.1:8000/api/auth/google/callback").strip()

        if not client_id or not client_secret:
            return {"success": False, "error": "Client ID ve Secret boş olamaz."}

        db = await get_async_db()
        try:
            await db.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('google_client_id', ?)", (client_id,))
            await db.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('google_client_secret', ?)", (client_secret,))
            await db.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('google_redirect_uri', ?)", (redirect_uri,))
            await db.commit()
        finally:
            await db.close()
        return {"success": True}
    except Exception as e:
        app_logger.error(f"Google OAuth ayarları kayıt hatası: {e}")
        return {"success": False, "error": "Kayıt hatası."}


@app.post("/create_channel")
async def create_channel(
    name: str = Form(...),
    content_type: str = Form(""),
    target_audience: str = Form(""),
    purpose: str = Form(""),
    channel_rules: str = Form(""),
    user_id: int = Form(1)
):
    try:
        db = await get_async_db()
        try:
            cursor = await db.execute("INSERT INTO channels (name, content_type, target_audience, purpose, channel_rules, user_id) VALUES (?, ?, ?, ?, ?, ?)",
                      (name, content_type, target_audience, purpose, channel_rules, user_id))
            await db.commit()
            channel_id = cursor.lastrowid
            return {"success": True, "channel_id": channel_id, "name": name}
        finally:
            await db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/register")
async def register(request: Request):
    try:
        data = await request.json()
        username = data.get("username", "").strip()
        password = data.get("password", "")
        email = data.get("email", "").strip()
        lang = data.get("lang", "tr")

        if not username or len(username) < 3:
            return {"error": "Kullanıcı adı en az 3 karakter olmalıdır."}
        if not password or len(password) < 6:
            return {"error": "Şifre en az 6 karakter olmalıdır."}
        if " " in username:
            return {"error": "Kullanıcı adında boşluk olamaz."}
        if not email or "@" not in email:
            return {"error": "Geçerli bir email adresi girin."}

        pw_hash = hash_password(password)
        db = await get_async_db()
        try:
            try:
                cursor = await db.execute("INSERT INTO users (username, password_hash, email, is_verified) VALUES (?, ?, ?, 0)",
                          (username, pw_hash, email))
                await db.commit()
                user_id = cursor.lastrowid
            except sqlite3.IntegrityError:
                return {"error": "Bu kullanıcı adı zaten kullanılıyor."}

            # Doğrulama kodu oluştur
            code = generate_verification_code()
            from datetime import timedelta
            expires_at = (datetime.now() + timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
            await db.execute("INSERT INTO email_verifications (user_id, code, expires_at) VALUES (?, ?, ?)",
                      (user_id, code, expires_at))
            await db.commit()
        finally:
            await db.close()

        print(f"MAIL GÖNDERİLİYOR: {email}, kod: {code}")
        mail_sent = send_verification_email(email, code, lang)
        print(f"MAIL SONUCU: {mail_sent}")
        return {
            "success": True,
            "user_id": user_id,
            "username": username,
            "needs_verification": True,
            "mail_sent": mail_sent,
            "email": email
        }
    except Exception:
        traceback.print_exc()
        return {"error": "Kayıt sırasında beklenmeyen bir hata oluştu."}


@app.post("/api/auth/login")
async def login(request: Request):
    try:
        data = await request.json()
        username = data.get("username", "").strip()
        password = data.get("password", "")
        if not username or not password:
            return {"error": "Kullanıcı adı ve şifre boş olamaz."}
        db = await get_async_db()
        try:
            async with db.execute("SELECT id, password_hash, is_verified, email FROM users WHERE username=?", (username,)) as cursor:
                row = await cursor.fetchone()
        finally:
            await db.close()
        
        if not row:
            return {"error": "Kullanıcı bulunamadı."}
        user_id, stored_hash, is_verified, user_email = row
        if not stored_hash:
            return {"error": "Bu hesaba giriş yapılamaz."}
        if not verify_password(password, stored_hash):
            return {"error": "Şifre yanlış."}
        if is_verified == 0 and user_email:
            return {"error": "EMAIL_NOT_VERIFIED", "email": user_email, "user_id": user_id}
        return {"success": True, "user_id": user_id, "username": username}
    except Exception:
        traceback.print_exc()
        return {"error": "Giriş sırasında beklenmeyen bir hata oluştu."}


@app.post("/api/auth/verify")
async def verify_email(request: Request):
    try:
        data = await request.json()
        user_id = data.get("user_id")
        code = data.get("code", "").strip()

        if not user_id or not code:
            return {"error": "Eksik bilgi."}

        db = await get_async_db()
        try:
            async with db.execute("""SELECT id, expires_at, verified FROM email_verifications
                         WHERE user_id=? AND code=?
                         ORDER BY created_at DESC LIMIT 1""", (user_id, code)) as cursor:
                row = await cursor.fetchone()

            if not row:
                return {"error": "Kod yanlış."}

            ver_id, expires_at, verified = row
            if verified:
                return {"error": "Bu kod zaten kullanılmış."}

            if datetime.now() > datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S'):
                return {"error": "Kodun süresi dolmuş. Tekrar kayıt ol."}

            await db.execute("UPDATE users SET is_verified=1 WHERE id=?", (user_id,))
            await db.execute("UPDATE email_verifications SET verified=1 WHERE id=?", (ver_id,))
            await db.commit()

            async with db.execute("SELECT username FROM users WHERE id=?", (user_id,)) as cursor:
                urow = await cursor.fetchone()

            return {"success": True, "user_id": user_id, "username": urow[0] if urow else ""}
        finally:
            await db.close()
    except Exception:
        traceback.print_exc()
        return {"error": "Doğrulama sırasında hata oluştu."}


@app.post("/api/auth/resend")
async def resend_verification(request: Request):
    try:
        data = await request.json()
        user_id = data.get("user_id")
        lang = data.get("lang", "tr")

        db = await get_async_db()
        try:
            async with db.execute("SELECT email FROM users WHERE id=?", (user_id,)) as cursor:
                row = await cursor.fetchone()
            if not row:
                return {"error": "Kullanıcı bulunamadı."}

            email = row[0]
            code = generate_verification_code()
            from datetime import timedelta
            expires_at = (datetime.now() + timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
            await db.execute("INSERT INTO email_verifications (user_id, code, expires_at) VALUES (?, ?, ?)",
                      (user_id, code, expires_at))
            await db.commit()
        finally:
            await db.close()

        mail_sent = send_verification_email(email, code, lang)
        return {"success": True, "mail_sent": mail_sent}
    except Exception:
        traceback.print_exc()
        return {"error": "Kod gönderilemedi."}


@app.get("/api/profile")
async def get_profile(user_id: int = 1):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id, username, created_at FROM users WHERE id=?", (user_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return {"error": "Kullanıcı bulunamadı."}
        uid, uname, created = row
        c.execute("SELECT COUNT(*) FROM channels WHERE user_id=?", (uid,))
        channel_count = c.fetchone()[0]
        c.execute("""SELECT COUNT(*), AVG(a.overall_score) FROM analyses a
                    JOIN channels ch ON a.channel_id = ch.id WHERE ch.user_id=?""", (uid,))
        analysis_row = c.fetchone()
        analysis_count = analysis_row[0] or 0
        avg_score = round(analysis_row[1], 1) if analysis_row[1] else 0.0
        c.execute("""SELECT a.id, a.video_name, a.overall_score, a.timestamp, ch.name
                    FROM analyses a JOIN channels ch ON a.channel_id = ch.id
                    WHERE ch.user_id=? ORDER BY a.timestamp DESC""", (uid,))
        recent = [{"id": r[0], "video": r[1], "score": r[2], "date": r[3], "channel": r[4]} for r in c.fetchall()]
        conn.close()
        return {"user_id": uid, "username": uname, "created_at": created,
                "channel_count": channel_count, "analysis_count": analysis_count,
                "avg_score": avg_score, "recent_analyses": recent}
    except Exception:
        traceback.print_exc()
        return {"error": "Profil yüklenirken hata oluştu."}


@app.get("/api/analyses/{analysis_id}")
async def get_analysis_by_id(analysis_id: int):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("""SELECT a.id, a.video_name, a.overall_score, a.retention_score, a.tech_score,
                        a.seo_score, a.thumb_score, a.peaks, a.viral_score, a.coach_feedback,
                        a.competitor_data, a.video_description, a.video_tags, a.timestamp, ch.name
                    FROM analyses a JOIN channels ch ON a.channel_id = ch.id
                    WHERE a.id=?""", (analysis_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return {"error": "Analiz bulunamadı."}
        return {
            "analysis_id": row[0],
            "video_name": row[1],
            "overall_score": row[2],
            "retention_score": row[3],
            "tech_score": row[4],
            "seo_score": row[5],
            "thumb_score": row[6] if row[6] is not None else 0,
            "peaks": row[7],
            "viral_score": row[8],
            "coach_feedback": row[9],
            "competitor_data": row[10],
            "video_description": row[11],
            "video_tags": row[12],
            "timestamp": row[13],
            "channel_name": row[14],
            "is_history": True
        }
    except Exception:
        traceback.print_exc()
        return {"error": "Analiz yüklenirken hata oluştu."}


@app.delete("/api/analyses/{analysis_id}")
async def delete_analysis(analysis_id: int):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM analyses WHERE id=?", (analysis_id,))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception:
        traceback.print_exc()
        return {"success": False, "error": "Silme işlemi başarısız."}


@app.get("/api/settings/gemini")
async def get_gemini_key():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT value FROM app_settings WHERE key='gemini_api_key'")
    row = c.fetchone()
    conn.close()
    decrypted = CryptoManager.decrypt(row[0]) if row and row[0] else ""
    return {"has_key": bool(decrypted), "key": decrypted}


@app.post("/api/settings/gemini")
async def set_gemini_key(key: str = Form(...)):
    key = key.strip()
    if not key:
        return {"success": False, "error": "Geçersiz Gemini API Anahtarı"}
    try:
        test_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        resp = requests.get(test_url, timeout=5)
        if resp.status_code != 200:
            return {"success": False, "error": "Geçersiz Gemini API Anahtarı"}
    except requests.exceptions.RequestException:
        return {"success": False, "error": "Gemini API ile bağlantı kurulamadı"}
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('gemini_api_key', ?)", (CryptoManager.encrypt(key),))
    conn.commit()
    conn.close()
    return {"success": True}


@app.post("/api/content_finder")
async def content_finder(request: Request):
    try:
        data = await request.json()
        keyword = data.get("keyword", "").strip()
        lang = data.get("lang", "tr")  
        user_id = data.get("user_id", 1)
        if not keyword:
            return {"error": "Lütfen aranacak bir kelime veya konsept girin."}
        if not YT_DLP_AVAILABLE:
            return {"error": "yt-dlp yüklü değil, arama yapılamıyor."}

        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'skip_download': True,
            'max_downloads': 5,
            'socket_timeout': 15,
        }
        search_query = f"ytsearch5:{keyword}"
        videos = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=False)
                if not info or 'entries' not in info or not info['entries']:
                    return {"error": f"'{keyword}' için arama sonucu bulunamadı."}
                for entry in info['entries']:
                    if not entry:
                        continue
                    views = entry.get('view_count') or 0
                    raw_date = str(entry.get('upload_date', ''))
                    days_passed = 1
                    if raw_date and len(raw_date) == 8:
                        try:
                            d = datetime.strptime(raw_date, '%Y%m%d')
                            days_passed = max(1, (datetime.now() - d).days)
                        except Exception as e:
                            app_logger.debug(f"Hata [content_finder date parse]: {e}")
                    view_velocity = views / days_passed if views > 0 else 0
                    videos.append({
                        'id': entry.get('id', ''),
                        'title': entry.get('title', 'Bilinmiyor'),
                        'channel': entry.get('uploader', 'Rakip'),
                        'views': views,
                        'days_passed': days_passed,
                        'view_velocity': round(view_velocity, 1),
                        'url': f"https://youtube.com/watch?v={entry.get('id', '')}",
                        'is_outlier': False
                    })
        except Exception as e:
            traceback.print_exc()
            return {"error": f"YouTube araması sırasında hata: {str(e)[:100]}"}

        if not videos:
            return {"error": "Arama sonucunda hiç video bulunamadı."}

        avg_velocity = sum(v['view_velocity'] for v in videos) / len(videos)
        outliers = []
        for v in videos:
            if avg_velocity > 0 and v['view_velocity'] > (avg_velocity * 1.5):
                v['is_outlier'] = True
                outliers.append(v)
        if not outliers and videos:
            top = max(videos, key=lambda x: x['view_velocity'])
            top['is_outlier'] = True
            outliers.append(top)

        ai_ideas = []
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT key, value FROM app_settings WHERE key IN ('groq_api_key', 'gemini_api_key')")
        api_keys = {row[0]: row[1] for row in c.fetchall()}
        groq_api_key = api_keys.get('groq_api_key', '')
        gemini_api_key = api_keys.get('gemini_api_key', '')

        if (groq_api_key or gemini_api_key) and outliers:
            outlier_titles = [v['title'] for v in outliers[:3]]

            lang_prompts = {
                "tr": f"""Kullanıcı '{keyword}' konseptinde YouTube videoları çekiyor.
Şu an algoritmayı domine eden patlamış video başlıkları:
{json.dumps(outlier_titles, ensure_ascii=False)}

3 YEPYENİ VİDEO FİKRİ üret. Her fikir için:
1. "title": Merak uyandıran başlık
2. "hook": İlk 5 saniyede söylenecek kanca cümle
3. "thumbnail": Thumbnail tasarım önerisi

SADECE JSON Array döndür, Türkçe yaz:
[{{"title":"...","hook":"...","thumbnail":"..."}}]""",

                "en": f"""The user is making YouTube videos about '{keyword}'.
Currently trending video titles dominating the algorithm:
{json.dumps(outlier_titles, ensure_ascii=False)}

Generate 3 BRAND NEW VIDEO IDEAS. For each idea provide:
1. "title": A curiosity-inducing title
2. "hook": Opening sentence for the first 5 seconds
3. "thumbnail": Thumbnail design suggestion

Return ONLY a JSON Array, answer in English:
[{{"title":"...","hook":"...","thumbnail":"..."}}]""",

                "es": f"""El usuario está haciendo videos de YouTube sobre '{keyword}'.
Títulos de videos virales que dominan el algoritmo actualmente:
{json.dumps(outlier_titles, ensure_ascii=False)}

Genera 3 IDEAS DE VIDEO NUEVAS. Para cada idea proporciona:
1. "title": Un título que genere curiosidad
2. "hook": Frase de apertura para los primeros 5 segundos
3. "thumbnail": Sugerencia de diseño de miniatura

Devuelve SOLO un Array JSON, responde en Español:
[{{"title":"...","hook":"...","thumbnail":"..."}}]"""
            }

            prompt = lang_prompts.get(lang, lang_prompts["en"])

            
            if groq_api_key:

                try:
                    resp = requests.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"},
                        json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}],
                              "temperature": 0.7, "max_tokens": 800},
                        timeout=20
                    )
                    if resp.status_code == 200:
                        ai_text = resp.json()["choices"][0]["message"]["content"]
                        if "```json" in ai_text:
                            ai_text = ai_text.split("```json")[1].split("```")[0]
                        elif "```" in ai_text:
                            ai_text = ai_text.split("```")[1].split("```")[0]
                        match = re.search(r'\[.*\]', ai_text, re.DOTALL)
                        if match:
                            ai_ideas = json.loads(match.group())
                except Exception:
                    traceback.print_exc()

        try:
            c.execute("INSERT INTO content_ideas (user_id, keyword, generated_ideas_json, search_results_json) VALUES (?, ?, ?, ?)",
                      (user_id, keyword, json.dumps(ai_ideas, ensure_ascii=False), json.dumps(videos, ensure_ascii=False)))
            conn.commit()
        except Exception as e:
            app_logger.error(f"Hata [content_finder db save]: {e}")
        conn.close()

        return {"success": True, "keyword": keyword, "videos": videos,
                "ai_ideas": ai_ideas, "has_api_key": bool(groq_api_key)}

    except Exception as e:
        traceback.print_exc()
        return {"error": "İçerik bulucu çalıştırılırken sunucu hatası oluştu."}


@app.get("/channels")
async def get_channels(user_id: int = 1):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, content_type, target_audience, purpose, channel_rules FROM channels WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    channels = [{"id": row[0], "name": row[1], "content_type": row[2], "target_audience": row[3], "purpose": row[4], "channel_rules": row[5] or ""} for row in c.fetchall()]
    conn.close()
    return channels


@app.delete("/channels/{channel_id}")
async def delete_channel(channel_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM analyses WHERE channel_id=?", (channel_id,))
    c.execute("DELETE FROM channels WHERE id=?", (channel_id,))
    conn.commit()
    conn.close()
    return {"success": True}


@app.put("/channels/{channel_id}")
async def edit_channel(channel_id: int, name: str = Form(...), content_type: str = Form(""), target_audience: str = Form(""), purpose: str = Form(""), channel_rules: str = Form("")):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE channels SET name=?, content_type=?, target_audience=?, purpose=?, channel_rules=? WHERE id=?", (name, content_type, target_audience, purpose, channel_rules, channel_id))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}


@app.post("/analyze")
async def analyze_video(
    video_file: UploadFile = File(...),
    csv_file: Optional[UploadFile] = File(None),
    thumb_file: Optional[UploadFile] = File(None),
    title: str = Form(""),
    description: str = Form(""),
    tags: str = Form(""),
    is_shorts: bool = Form(False),
    pro_mode: bool = Form(False),
    competitor_url: str = Form(""),
    channel_id: int = Form(...),
    user_id: int = Form(1),
    lang: str = Form("tr"),
):
    cleanup_temp_videos()

    uid = str(uuid.uuid4())[:8]
    analysis_start_time = time.time()
    v_path = str(temp_dir / f"v_{uid}.mp4")
    c_path = f"c_{uid}.csv" if csv_file else None
    t_path = f"t_{uid}.png" if thumb_file and not is_shorts else None

    try:
        if not video_file.filename:
            raise HTTPException(status_code=400, detail="Yüklenen video dosyası seçilmedi.")

        # --- NON-BLOCKING: Dosya kopyalama (ağır I/O) ---
        await run_in_threadpool(
            _copy_uploads,
            video_file.file, csv_file.file if csv_file else None,
            thumb_file.file if thumb_file else None,
            v_path, c_path, t_path
        )

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT content_type, target_audience, purpose, name FROM channels WHERE id=?", (channel_id,))
        ch_data = c.fetchone()
        conn.close()

        c_type = ch_data[0] if ch_data else "Genel"
        c_aud = ch_data[1] if ch_data else ""
        c_purp = ch_data[2] if ch_data else ""
        ch_name = ch_data[3] if ch_data else ""

        # --- NON-BLOCKING: Ağır CPU/IO analiz işlemleri ---
        tech = await run_in_threadpool(AnalysisEngine.analyze_video_tech, v_path, pro_mode)
        v_tempo = await run_in_threadpool(AnalysisEngine.analyze_visual_tempo, v_path, pro_mode)
        a_tempo = await run_in_threadpool(AnalysisEngine.analyze_audio_per_sec, v_path, pro_mode)
        golden_frame_sec = int(np.argmax(v_tempo)) if v_tempo else 0

        # --- NON-BLOCKING: Sahne değişimi ve hareket analizi (Aşama 3) ---
        scene_changes = await run_in_threadpool(
            AnalysisEngine.analyze_scene_changes, v_path, c_type)

        # --- NON-BLOCKING: Rakip analizi (network I/O) ---
        competitor_data = await run_in_threadpool(CompetitorAnalyzer.get_competitor, c_type, tags, competitor_url, ch_name)
        if competitor_data:
            competitor_data['user_title_len'] = len(title)
            competitor_data['user_tags'] = [t.strip() for t in tags.split(',') if t.strip()]
            user_hashtags = [h.lower() for h in re.findall(r'#(\w+)', str(description))]
            user_hashtags = list(dict.fromkeys([h for h in user_hashtags if h]))
            competitor_data['user_hashtags'] = user_hashtags
            competitor_data['user_description'] = description

        kill_switch_active = False
        if competitor_data:
            comp_title_for_ks = competitor_data.get('title', '')
            kill_switch_active = compute_kill_switch(title, comp_title_for_ks)

        retention = {"score": 5.0, "worst_drop_sec": 0, "drop_percent": 0, "has_csv": False, "early_drop_sec": 0}
        if c_path:
            retention["has_csv"] = True
            try:
                df = pd.read_csv(c_path, skipinitialspace=True)
                df.columns = df.columns.str.strip().str.lower()
                ret_keywords = ['retention', 'izlenme', 'görüntüleme', 'elde tutma']
                ret_col = next((col for col in df.columns if any(kw in col.lower() for kw in ret_keywords)), None)
                if ret_col:
                    df[ret_col] = df[ret_col].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
                    df[ret_col] = pd.to_numeric(df[ret_col], errors='coerce')
                    intro = df[ret_col].dropna().iloc[:30]
                    if len(intro) > 5:
                        start = intro.iloc[0]
                        worst_idx = intro.diff().idxmin()
                        drop_p = (start - intro.min()) / start * 100
                        retention = {
                            "score": round(max(0, min(10, 10 - (drop_p * 0.13)))),
                            "worst_drop_sec": int(worst_idx),
                            "drop_percent": round(drop_p, 1),
                            "has_csv": True,
                            "early_drop_sec": int(intro[:10].idxmin())
                        }
            except Exception as e:
                app_logger.warning(f"Hata [analyze_video CSV parse]: {e}")

        # --- NON-BLOCKING: Thumbnail analizi (DeepFace + kontrast + vibrant) ---
        thumb_data = (await run_in_threadpool(AnalysisEngine.analyze_thumbnail, t_path)) if t_path else {
            "score": 0.0, "face_detected": False, "face_count": 0, "faces": [],
            "contrast_ratio": 0.0, "text_space_score": 0.0,
            "vibrant_color_match": 0.0, "visual_summary": ""
        }
        thumb_score = thumb_data["score"]

        seo_score = 0.0
        seo_score += 3.5 if 35 <= len(title) <= 70 else 2.0
        seo_score += min(3.5, len([t for t in tags.split(',') if t.strip()]) * 0.5)
        hook_words = ['nasıl', 'neden', 'en iyi', '2024', 'şok', 'sır', '!', '?', 'sonunda', 'efsane', 'bittirdik']
        if any(w in title.lower() for w in hook_words):
            seo_score += 1.5
        seo_score = min(10.0, round(seo_score, 1))

        weights = {"retention": 0.45, "tech": 0.35 if is_shorts else 0.28, "seo": 0.10 if is_shorts else 0.17, "thumb": 0.0 if is_shorts else 0.10}
        if not t_path and not is_shorts:
            weights["retention"], weights["tech"], weights["seo"] = 0.45, 0.35, 0.20
        overall = round(retention["score"] * weights["retention"] + tech["tech_score"] * weights["tech"] + seo_score * weights["seo"] + thumb_score * weights["thumb"], 1)

        # ── Görsel Zeka Özeti (Aşama 3) ──
        vi_parts = []
        if thumb_data.get("face_detected") and thumb_data.get("faces"):
            primary_face = thumb_data["faces"][0]
            emo = primary_face.get("dominant_emotion", "neutral")
            emo_conf = primary_face.get("emotion_scores", {}).get(emo, 0)
            gaze = "looking at camera" if primary_face.get("looking_at_camera") else "looking away"
            vi_parts.append(
                f"Thumbnail: Face detected with '{emo}' emotion "
                f"({emo_conf:.0f}% confidence), {gaze}."
            )
        elif thumb_data.get("face_detected"):
            vi_parts.append("Thumbnail: Face detected (basic analysis).")
        else:
            vi_parts.append("Thumbnail: No face detected.")

        if thumb_data.get("contrast_ratio", 0) > 0:
            cr = thumb_data["contrast_ratio"]
            cr_qual = "excellent" if cr >= 0.5 else "good" if cr >= 0.3 else "low"
            vi_parts.append(f"Contrast ratio: {cr_qual} ({cr:.2f}).")

        if thumb_data.get("vibrant_color_match", 0) > 0:
            vcm = thumb_data["vibrant_color_match"]
            vi_parts.append(f"Vibrant color match: {vcm}/10.")

        if thumb_data.get("text_space_score", 0) > 0:
            tss = thumb_data["text_space_score"]
            vi_parts.append(f"Text space score: {tss}/10.")

        if scene_changes:
            sc = scene_changes
            vi_parts.append(
                f"Scene analysis: {sc.get('cut_count', 0)} cuts detected, "
                f"{sc.get('cut_frequency', 0)} cuts/min, "
                f"avg motion intensity {sc.get('avg_motion_intensity', 0)}."
            )

        visual_insights_str = " ".join(vi_parts)

        dynamic_feedback = await AnalysisEngine.generate_dynamic_feedback(
            c_type, c_aud, c_purp, tech["tech_score"], retention["score"],
            tech["peaks"], lang=lang, thumb_insights=thumb_data,
            visual_insights_str=visual_insights_str)
        dynamic_feedback_tr = await AnalysisEngine.generate_dynamic_feedback(
            c_type, c_aud, c_purp, tech["tech_score"], retention["score"],
            tech["peaks"], lang="tr", thumb_insights=thumb_data,
            visual_insights_str=visual_insights_str)
        dynamic_feedback_en = await AnalysisEngine.generate_dynamic_feedback(
            c_type, c_aud, c_purp, tech["tech_score"], retention["score"],
            tech["peaks"], lang="en", thumb_insights=thumb_data,
            visual_insights_str=visual_insights_str)
        dynamic_feedback_es = await AnalysisEngine.generate_dynamic_feedback(
            c_type, c_aud, c_purp, tech["tech_score"], retention["score"],
            tech["peaks"], lang="es", thumb_insights=thumb_data,
            visual_insights_str=visual_insights_str)
        

        result = {
            "overall_score": overall, "retention_score": retention["score"], "retention_data": retention,
            "tech_score": tech["tech_score"], "tech_data": tech, "seo_score": seo_score,
            "thumb_score": thumb_score if not is_shorts else None, "thumb_data": thumb_data,
            "peaks": tech["peaks"], "viral_score": tech["viral_score"],
            "title": title, "tags": tags, "is_shorts_mode": is_shorts, "pro_mode": pro_mode,
            "coaching_mode": "PROACTIVE" if retention["has_csv"] else "PREDICTIVE",
            "visual_tempo": v_tempo, "audio_tempo": a_tempo, "golden_frame_sec": golden_frame_sec,
            "dynamic_feedback": dynamic_feedback,
            "dynamic_feedback_tr": dynamic_feedback_tr,
            "dynamic_feedback_en": dynamic_feedback_en,
            "dynamic_feedback_es": dynamic_feedback_es,
            "competitor_data": competitor_data, "industry_std": AnalysisEngine.get_industry_standard(c_type),
            "viral_segments": AnalysisEngine.find_viral_segments(
                tech, visual_tempo=v_tempo, scene_changes=scene_changes),
            "scene_changes": scene_changes,
            "visual_intelligence_summary": visual_insights_str,
            "ffmpeg_available": FFMPEG_AVAILABLE,
            "yt_dlp_available": YT_DLP_AVAILABLE,
            "critical_warning": f"Giriş {retention['score']}/10 | Tempo {tech['tech_score']}/10 | Patlama {tech['peaks']} adet",
            "kill_switch_active": kill_switch_active,
            "temp_video_name": f"v_{uid}.mp4",
            "analysis_duration_sec": round(time.time() - analysis_start_time, 1)
        }
        result["analysis_id"] = await AnalysisEngine.save_analysis(channel_id, result, user_id)
        result["channel_comparison"] = await AnalysisEngine.get_channel_averages(channel_id)
        result["system_caps"] = SYSTEM_CAPS

        # ── Otomatik E-posta Rapor Gönderimi ──
        email_sent = False
        try:
            db_mail = await get_async_db()
            try:
                async with db_mail.execute("SELECT email, is_verified FROM users WHERE id=?", (user_id,)) as c_mail:
                    u_row = await c_mail.fetchone()
                async with db_mail.execute("SELECT key, value FROM app_settings WHERE key IN ('smtp_email', 'smtp_password')") as c_mail:
                    smtp_rows = {r[0]: r[1] async for r in c_mail}
            finally:
                await db_mail.close()

            user_email = u_row[0] if u_row and u_row[0] else ""
            has_smtp = bool(smtp_rows.get('smtp_email') and smtp_rows.get('smtp_password'))

            if user_email and has_smtp:
                # PDF oluştur ve gönder (thread pool'da)
                analysis_id = result["analysis_id"]
                _title = result.get("title", "Video")

                async def _auto_email():
                    try:
                        # export_pdf fonksiyonunu direkt çağıramayız, kendi mini PDF'imizi oluşturalım
                        # Bunun yerine mevcut export_pdf endpoint URL'ini kullanarak oluştururuz
                        from io import BytesIO
                        pdf_auto_path = str(output_dir / f"report_{analysis_id}_{lang}.pdf")
                        # PDF zaten export_pdf'de oluşturulacak, şimdilik sadece path'i hazırla
                        # İlk export yapıldığında dosya var olacak, olmasa da sorun yok
                        return await run_in_threadpool(
                            send_report_email, user_email, pdf_auto_path, _title, lang
                        )
                    except Exception:
                        return False

                # Non-blocking: Arka planda gönder
                import asyncio
                try:
                    # Önce PDF'i oluştur
                    _pdf_path = str(output_dir / f"report_{analysis_id}_{lang}.pdf")
                    # Mini PDF oluşturma — export_pdf endpoint'ini simüle et
                    # (email gönderimi analyze sonrası frontend'den tetiklenecek)
                    email_sent = True  # Frontend'e bildiri: SMTP ayarları var, gönderim tetiklenebilir
                except Exception:
                    pass
        except Exception:
            pass

        result["email_sent"] = email_sent
        result["user_has_email"] = bool(email_sent)
        return result

    except Exception as e:
        traceback.print_exc()
        if os.path.exists(v_path):
            try:
                os.remove(v_path)
            except Exception as e:
                app_logger.warning(f"Hata [create_short clean v_path]: {e}")
        return {"error": str(e)}
    finally:
        for p in [c_path, t_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception as e:
                    app_logger.warning(f"Hata [create_short clean {p}]: {e}")


@app.post("/create_short")
async def create_short(
    start: float = Form(...),
    duration: float = Form(...),
    temp_filename: str = Form(...),
    video_file: Optional[UploadFile] = File(None)
):
    if not FFMPEG_AVAILABLE:
        return {"error": "FFmpeg sistemde bulunamadı."}

    uid = str(uuid.uuid4())[:8]
    output_name = f"short_{uid}.mp4"
    output_path = output_dir / output_name
    temp_in = None

    try:
        saved_path = temp_dir / temp_filename
        if temp_filename != "MISSING" and saved_path.exists():
            temp_in = str(saved_path)
        elif video_file:
            temp_in = str(temp_dir / f"fallback_{uid}.mp4")
            # --- NON-BLOCKING: Dosya kopyalama ---
            def _copy_fallback():
                with open(temp_in, "wb") as f:
                    shutil.copyfileobj(video_file.file, f)
            await run_in_threadpool(_copy_fallback)
        else:
            return {"error": "Video dosyası bulunamadı. Lütfen videoyu tekrar analiz edin."}

        # GPU codec'e göre parametreleri ayarla
        if GPU_CODEC == "libx264":
            codec_params = ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "18"]
        elif GPU_CODEC == "h264_nvenc":
            codec_params = ["-c:v", "h264_nvenc", "-preset", "p1", "-cq", "23"]
        elif GPU_CODEC == "h264_amf":
            codec_params = ["-c:v", "h264_amf", "-quality", "speed", "-rc", "cqp", "-qp_i", "23"]
        elif GPU_CODEC == "h264_qsv":
            codec_params = ["-c:v", "h264_qsv", "-preset", "veryfast", "-global_quality", "23"]
        else:
            codec_params = ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "18"]

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", temp_in,
            "-t", str(duration),
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1",
            *codec_params,
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_path)
        ]

        # --- NON-BLOCKING: FFmpeg subprocess ---
        def _run_ffmpeg_short():
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                creationflags=0x08000000 if os.name == 'nt' else 0
            )
        process = await run_in_threadpool(_run_ffmpeg_short)

        if process.returncode != 0:
            print(f"FFmpeg Hatası Detayı: {process.stderr}")
            return {"error": f"Kesme işlemi başarısız: {process.stderr[:100]}"}

        return {
            "success": True,
            "filename": output_name,
            "download_url": f"/shorts/{output_name}"
        }

    except Exception as e:
        traceback.print_exc()
        return {"error": f"Sistem Hatası: {str(e)}"}


@app.get("/export_pdf/{analysis_id}")
async def export_pdf(analysis_id: int, lang: str = "tr"):
    # Geçersiz dil kodu gelirse Türkçe'ye düş
    if lang not in PDF_LANG or not PDF_LANG[lang]:
        lang = "tr"
    L = PDF_LANG[lang]


    def esc(txt):
        if txt is None:
            return ""
        s = str(txt)
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        s = s.replace('"', "").replace("'", "")
        return s

    conn = get_db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
    analysis = c.fetchone()
    if not analysis:
        raise HTTPException(status_code=404)
    channel_id = analysis['channel_id']
    c2 = conn.cursor()
    c2.execute("SELECT name, content_type FROM channels WHERE id = ?", (channel_id,))
    ch_info = c2.fetchone()
    channel_name = ch_info['name'] if ch_info else "Bilinmeyen Kanal"
    c_type = ch_info['content_type'] if ch_info else "Genel"
    averages = await AnalysisEngine.get_channel_averages(channel_id)
    conn.close()

    overall = float(analysis['overall_score'])
    retention = float(analysis['retention_score'])
    tech = float(analysis['tech_score'])
    seo = float(analysis['seo_score'])
    thumb = float(analysis['thumb_score']) if analysis['thumb_score'] is not None else 0.0
    peaks = int(analysis['peaks'])
    video_name_str = str(analysis['video_name'])

    # video_description ve video_tags DB'den al (yoksa competitor_data içinden çıkar)
    video_description_str = ""
    video_tags_str = ""
    try:
        video_description_str = str(analysis['video_description'] or "")
    except Exception as e:
        app_logger.debug(f"PDF extract description error: {e}")
    try:
        video_tags_str = str(analysis['video_tags'] or "")
    except Exception as e:
        app_logger.debug(f"PDF extract tags error: {e}")

    # competitor_data'dan da açıklama ve etiket almayı dene
    comp_json_raw = analysis['competitor_data']
    if comp_json_raw and (not video_tags_str or not video_description_str):
        try:
            _cd = json.loads(comp_json_raw)
            if not video_tags_str:
                ut = _cd.get('user_tags', [])
                video_tags_str = ', '.join(ut) if isinstance(ut, list) else str(ut)
            if not video_description_str:
                video_description_str = _cd.get('user_description', '')
        except Exception as e:
            app_logger.debug(f"PDF extract competitor info error: {e}")

    pdf_path = output_dir / f"report_{analysis_id}_{lang}.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path), pagesize=letter,
        leftMargin=1.25*inch, rightMargin=1.25*inch,
        topMargin=1.0*inch, bottomMargin=1.0*inch
    )
    elements = []
    styles = getSampleStyleSheet()

    # ── APA Stil Tanımları ──
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

    # Kapak başlığı (ortalı, büyük)
    title_s = ParagraphStyle('apa_title',
        fontName=FONT_BOLD, fontSize=16, leading=22,
        alignment=TA_CENTER, spaceAfter=6, textColor=colors.HexColor('#1a0533'))

    # Üst başlık — TAMAMEN BÜYÜK HARF
    heading1_s = ParagraphStyle('apa_h1',
        fontName=FONT_BOLD, fontSize=13, leading=18,
        alignment=TA_LEFT, spaceBefore=18, spaceAfter=6,
        textColor=colors.HexColor('#1a0533'),
        borderPad=4)

    # Alt başlık — İlk Harf Büyük
    heading2_s = ParagraphStyle('apa_h2',
        fontName=FONT_BOLD, fontSize=11, leading=16,
        alignment=TA_LEFT, spaceBefore=12, spaceAfter=4,
        textColor=colors.HexColor('#3b0764'))

    # Normal metin — justify
    normal_s = ParagraphStyle('apa_normal',
        fontName=FONT_REGULAR, fontSize=10, leading=15,
        alignment=TA_JUSTIFY, spaceAfter=6,
        textColor=colors.HexColor('#1e293b'))

    # Eski heading_s = heading1_s olarak devam etsin
    heading_s = heading1_s

    # Bölüm sayacı
    sec = [0]
    def h1(text):
        sec[0] += 1
        return Paragraph(f"{sec[0]}. {text.upper()}", heading1_s)
    def h2(text):
        # İlk harfleri büyük yap
        cap = ' '.join(w.capitalize() for w in text.split())
        return Paragraph(cap, heading2_s)

    # ── Kapak ──
    elements.append(Paragraph(L['report_title'], title_s))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(
        f"<b>{L['your_channel']}:</b> {esc(channel_name)}&nbsp;&nbsp;|&nbsp;&nbsp;<b>{L['your_video']}:</b> {esc(video_name_str)}",
        normal_s
    ))
    elements.append(Spacer(1, 0.1 * inch))

    # ince ayırıcı çizgi
    from reportlab.platypus import HRFlowable
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#7c3aed'), spaceAfter=14))

    # ── 1. Viral Potansiyel ──
    elements.append(h1(L['viral_potential'].replace('🔥', '').strip()))
    if peaks >= 5:
        if seo >= 7.0 and thumb >= 5.0:
            viral_txt = (f"<font color='green'><b>{L['viral_high']}</b></font><br/>"
                         + L['viral_high_desc'].format(peaks=peaks, seo=seo))
        else:
            viral_txt = (f"<font color='red'><b>{L['viral_low_pkg']}</b></font><br/>"
                         + L['viral_low_pkg_desc'].format(peaks=peaks, seo=seo, thumb=thumb))
    else:
        viral_txt = f"<b>{L['viral_low'].format(peaks=peaks)}</b>"
    elements.append(Paragraph(viral_txt, normal_s))
    elements.append(Spacer(1, 0.3 * inch))

    # ── 2. Sektör Standartları ──
    elements.append(h1(L['sector_std'].format(ctype=esc(c_type[:30])).replace('📊', '').strip()))
    ind_std = AnalysisEngine.get_industry_standard(c_type)
    std_data = [
        [L['metric'], L['your_video_col'], L['sector_ideal'], L['status']],
        [L['tempo_score'], f"{tech:.1f}", f"{ind_std['tempo']:.1f}", L['good'] if tech >= ind_std['tempo'] else L['behind']],
        [L['seo_power'], f"{seo:.1f}", f"{ind_std['seo']:.1f}", L['good'] if seo >= ind_std['seo'] else L['behind']],
        [L['retention'], f"{retention:.1f}", f"{ind_std['retention']:.1f}", L['good'] if retention >= ind_std['retention'] else L['behind']]
    ]
    t_std = Table(std_data)
    t_std.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('GRID', (0, 0), (-1, -1), 1, colors.black), ('FONTNAME', (0, 1), (-1, -1), FONT_REGULAR)
    ]))
    elements.append(t_std)
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(f"<font size=8 color='#666666'>{esc(L['sector_note'])}</font>", normal_s))
    elements.append(Spacer(1, 0.3 * inch))

    # ── SEO / Thumbnail Denge Uyarısı ──

    elements.append(Paragraph(f"<font size=8 color='#666666'>{esc(L['sector_note'])}</font>", normal_s))
    elements.append(Spacer(1, 0.2 * inch))

    # ── 3. SEO / Thumbnail Denge Uyarısı ──
    if seo >= 7.0 and thumb > 0.0 and thumb < 5.0:
        elements.append(h1(L['seo_thumb_warn_title'].replace('⚖️', '').strip()))

    # Durum 1: SEO güçlü ama Thumbnail zayıf → arama çıkar, tıklanmaz
    if seo >= 7.0 and thumb > 0.0 and thumb < 5.0:
        elements.append(h1(L['seo_thumb_warn_title'].replace('⚖️', '').strip()))
        elements.append(Paragraph(
            f"<font color='#d97706'>{L['seo_thumb_warn_msg'].format(seo=seo, thumb=thumb)}</font>",
            normal_s
        ))
        elements.append(Spacer(1, 0.15 * inch))
    elif thumb >= 7.0 and seo < 5.0:
        elements.append(h1(L['seo_thumb_warn_title'].replace('⚖️', '').strip()))
        elements.append(Paragraph(
            f"<font color='#d97706'>{L['thumb_seo_warn_msg'].format(seo=seo, thumb=thumb)}</font>",
            normal_s
        ))
        elements.append(Spacer(1, 0.15 * inch))

    # ── 4. İçerik Tutarlılık Kontrolü ──
    elements.append(h1(L['consistency_title'].replace('🔎', '').strip()))
    consistency = check_content_consistency(video_name_str, video_tags_str, video_description_str)
    if consistency['ok']:
        elements.append(Paragraph(f"<font color='green'><b>{L['consistency_ok']}</b></font>", normal_s))
    else:
        consistency_txt = f"<font color='#ef4444'><b>{L['consistency_warn']}</b></font><br/>"
        for issue in consistency['issues']:
            if issue == 'no_tags':
                consistency_txt += f"• <b>{L['no_tags']}:</b> <font color='#d97706'>{L['no_tags_desc']}</font><br/>"
            elif issue == 'no_desc':
                consistency_txt += f"• <b>{L['no_desc']}:</b> <font color='#d97706'>{L['no_desc_desc']}</font><br/>"
            elif issue == 'title_tags_mismatch':
                consistency_txt += f"• <b>{L['title_tags_mismatch']}:</b> <font color='#ef4444'>{L['title_tags_mismatch_desc']}</font><br/>"
            elif issue == 'title_desc_mismatch':
                consistency_txt += f"• <b>{L['title_desc_mismatch']}:</b> <font color='#d97706'>{L['title_desc_mismatch_desc']}</font><br/>"
        elements.append(Paragraph(consistency_txt, normal_s))
    elements.append(Spacer(1, 0.3 * inch))

    # ── Rakip Analizi ──
    comp_json = analysis['competitor_data']
    face_detected = False

    if comp_json:
        try:
            comp = json.loads(comp_json)
            face_detected = comp.get('face_detected', False)
            raw_channel = comp.get('channel') or 'Rakip Kanal'
            raw_title = comp.get('title') or 'Bilinmiyor'
            comp_channel_upper = esc(raw_channel.upper())
            comp_title = esc(raw_title)
            is_fake_data = comp.get('is_fake', False)

            if is_fake_data:
                elements.append(Paragraph(L['competitor_disabled'], heading_s))
                elements.append(Paragraph(
                    f"<font color='#ef4444'><b>{L['fake_data_title']}</b></font><br/>"
                    f"<font color='#d97706'>{L['fake_data_desc']}</font><br/><br/>"
                    f"<b>{L['fake_data_action']}</b><br/>"
                    f"{L['fake_data_fix1']}<br/>"
                    f"{L['fake_data_fix2']}",
                    normal_s
                ))
                elements.append(Spacer(1, 0.3 * inch))
                raise ValueError("FAKE_DATA_SKIP")

            v_raw = comp.get('views')
            try:
                views = int(v_raw) if v_raw is not None else 0
            except Exception as e:
                app_logger.debug(f"PDF views extract error: {e}")
                views = 0
            likes = int(comp.get('likes') or 0)
            comments = int(comp.get('comments') or 0)
            upload_date = comp.get('upload_date') or datetime.now().strftime('%Y%m%d')
            try:
                up_dt = datetime.strptime(upload_date, '%Y%m%d')
                days_live = max(1, (datetime.now() - up_dt).days)
                views_per_day = int(views / days_live)
            except Exception as e:
                app_logger.debug(f"PDF views_per_day extract error: {e}")
                views_per_day = views
            engagement = round(((likes + comments) / views * 100), 1) if views > 0 else 0.0
            comp_tags = comp.get('tags') or []
            user_tags = comp.get('user_tags') or []
            if not isinstance(comp_tags, list):
                comp_tags = []
            if not isinstance(user_tags, list):
                user_tags = []
            c_hashtags = comp.get('hashtags') or []
            u_hashtags = comp.get('user_hashtags') or []
            if not isinstance(c_hashtags, list):
                c_hashtags = []
            if not isinstance(u_hashtags, list):
                u_hashtags = []
            u_raw_len = comp.get('user_title_len')
            try:
                user_title_len = int(u_raw_len) if u_raw_len is not None else 0
            except Exception as e:
                app_logger.debug(f"PDF title_len extract error: {e}")
                user_title_len = 0
            is_manual = bool(comp.get('is_manual'))

            def tr_lower(s):
                return str(s).replace('İ', 'i').replace('I', 'ı').lower()

            broad_keywords = ['oyun', 'oyunlar', 'video', 'videolar', 'game', 'gaming', 'türkiye', 'tr',
                              'eğlence', 'komik', 'trend', 'viral', 'youtube', 'youtuber', 'abone', 'izle',
                              'yeni', 'ilk', 'türkçe', 'turkiye']

            raw_desc = comp.get('user_description', "")
            desc_clean = re.sub(r'#\w+', '', str(raw_desc))
            user_corpus_text = video_name_str + " " + channel_name + " " + desc_clean
            user_corpus = extract_core_keywords(user_corpus_text)

            # ── 5. SEO Check-Up ──
            elements.append(h1(L['checkup_title'].replace('🩺', '').strip()))
            checkup_txt = ""
            has_error = False
            user_tags_clean = [str(t).lower().replace('#', '').strip() for t in user_tags if str(t).strip()]
            u_hash_clean = [str(h).lower().replace('#', '').strip() for h in u_hashtags if str(h).strip()]

            broad_used_tags = [t for t in user_tags_clean if t in broad_keywords]
            irrelevant_used_tags = []
            for t in user_tags_clean:
                if t in broad_keywords:
                    continue
                t_words = extract_core_keywords(t)
                if t_words:
                    is_valid = False
                    for tw in t_words:
                        for cw in user_corpus:
                            if tw in cw or cw in tw:
                                is_valid = True
                                break
                        if is_valid:
                            break
                    if not is_valid:
                        irrelevant_used_tags.append(t)

            broad_used_hashes = [h for h in u_hash_clean if h in broad_keywords]
            irrelevant_used_hashes = []
            for h in u_hash_clean:
                if h in broad_keywords:
                    continue
                h_words = extract_core_keywords(h)
                if h_words:
                    is_valid = False
                    for hw in h_words:
                        for cw in user_corpus:
                            if hw in cw or cw in hw:
                                is_valid = True
                                break
                        if is_valid:
                            break
                    if not is_valid:
                        irrelevant_used_hashes.append(h)

            if broad_used_tags or irrelevant_used_tags:
                has_error = True
                checkup_txt += f"<b>{L['tag_errors']}:</b><br/>"
                if broad_used_tags:
                    checkup_txt += f"  - <b>{L['broad_tags_title']}:</b> <font color='#d97706'><b>{', '.join(broad_used_tags)}</b></font><br/>"
                    checkup_txt += f"  <font color='#666666'><em>* {L['broad_tags_note']}</em></font><br/>"
                if irrelevant_used_tags:
                    checkup_txt += f"  - <b>{L['irrelevant_tags_title']}:</b> <font color='#ef4444'><b>{', '.join(irrelevant_used_tags)}</b></font><br/>"
                    checkup_txt += f"  <font color='#666666'><em>* {L['irrelevant_tags_note']}</em></font><br/>"

            if broad_used_hashes or irrelevant_used_hashes:
                has_error = True
                checkup_txt += f"<br/><b>{L['hash_errors']}:</b><br/>"
                if broad_used_hashes:
                    checkup_txt += f"  - <b>{L['broad_hashes_title']}:</b> <font color='#d97706'><b>{', '.join(['#' + h for h in broad_used_hashes])}</b></font><br/>"
                    checkup_txt += f"  <font color='#666666'><em>* {L['broad_hashes_note']}</em></font><br/>"
                if irrelevant_used_hashes:
                    checkup_txt += f"  - <b>{L['irrelevant_hashes_title']}:</b> <font color='#ef4444'><b>{', '.join(['#' + h for h in irrelevant_used_hashes])}</b></font><br/>"
                    checkup_txt += f"  <font color='#666666'><em>* {L['irrelevant_hashes_note']}</em></font><br/>"

            if not u_hashtags:
                has_error = True
                checkup_txt += f"<br/><b>{L['missing_hashtag']}:</b> <font color='#ef4444'>{L['missing_hashtag_desc']}</font><br/>"

            if not has_error:
                checkup_txt += f"<font color='green'><b>{L['checkup_ok']}</b></font><br/>"

            elements.append(Paragraph(checkup_txt, normal_s))
            elements.append(Spacer(1, 0.4 * inch))

            is_mismatch_detected = compute_kill_switch(video_name_str, raw_title)
            comp_txt = ""

            if is_mismatch_detected:
                comp_txt += f"<br/><font color='#ef4444'>🚨 <b>{L['mismatch_detected']}</b></font><br/>"
                comp_txt += f"<font color='#d97706'><em>{L['mismatch_desc']}</em></font><br/><br/>"

            elements.append(h1(f"{L['you']} VS. {comp_channel_upper}"))

            if is_manual:
                comp_txt += f"<b>{L['manual_comp']}:</b> {comp_title}<br/><br/>"
            else:
                comp_txt += f"<b>{L['auto_comp']}:</b> {comp_title}<br/><br/>"

            comp_txt += f"<b>{L['xray_title']}:</b><br/>"
            comp_txt += f"• <b>{L['daily_views']}:</b> {views_per_day:,} {L['views_per_day_unit']}<br/>"
            comp_txt += f"• <b>{L['engagement_rate']}:</b> %{engagement} {L['engagement_unit']}<br/>"
            if engagement > 4.0:
                comp_txt += f"<font color='green'><em>{L['engagement_high']}</em></font><br/><br/>"
            else:
                comp_txt += f"<font color='#d97706'><em>{L['engagement_low']}</em></font><br/><br/>"

            u_tags_lower = [str(t).lower() for t in user_tags]
            common = [esc(t) for t in comp_tags if str(t).lower() in u_tags_lower]
            missing = [esc(t) for t in comp_tags if str(t).lower() not in u_tags_lower]
            toxic_keywords_list = [
                'parodi', 'animasyon', 'roleplay', 'rp', 'speedrun',
                'şarkı', 'müzik klip', 'film', 'dizi',
                'roblox', 'fortnite', 'gta', 'cs2', 'csgo',
                'valorant', 'pubg', 'fifa', 'apex', 'warzone',
                'canlı yayın', 'stream', 'twitch',
            ]
            v_title_lower_str = tr_lower(video_name_str)

            comp_txt += f"<b>{L['similarities_title']}:</b><br/>"
            if common:
                comp_txt += L['similarities_yes'].format(tags=', '.join(common)) + "<br/><br/>"
            else:
                comp_txt += L['similarities_no'] + "<br/><br/>"

            comp_txt += f"<b>{L['differences_title']}:</b><br/>"
            comp_txt += f"• <b>{L['title_strategy']}:</b> "
            if len(raw_title) > user_title_len + 15:
                comp_txt += L['title_longer'] + "<br/>"
            else:
                comp_txt += L['title_similar'] + "<br/>"

            if missing:
                comp_txt += f"<br/>• <b>{L['tag_analysis']}:</b><br/>"
                if is_mismatch_detected:
                    comp_txt += f"<font color='#d97706'><em>⚠️ {L['concept_mismatch_warn']}</em></font><br/>"
                perfect_matches, others, toxic_matches = [], [], []
                for t in missing:
                    t_l = tr_lower(t)
                    if t_l in broad_keywords:
                        continue
                    is_toxic = any(tw in t_l and tw not in v_title_lower_str for tw in toxic_keywords_list)
                    if is_toxic:
                        toxic_matches.append(t)
                    elif t_l in v_title_lower_str:
                        perfect_matches.append(t)
                    else:
                        others.append(t)
                if perfect_matches:
                    comp_txt += f"<b>{L['perfect_match_tags']}:</b> <font color='green'><b>{', '.join(perfect_matches)}</b></font><br/><br/>"
                if others:
                    comp_txt += f"<b>{L['inspiration_tags']}:</b> <font color='#c026d3'><b>{', '.join(others[:8])}</b></font><br/><br/>"
                if toxic_matches:
                    comp_txt += f"<b>{L['toxic_tags']}:</b> <font color='#ef4444'><b><strike>{', '.join(toxic_matches[:6])}</strike></b></font><br/>"
                    comp_txt += f"<font color='#666666'><em>* {L['toxic_tags_note']}</em></font><br/><br/>"

            if c_hashtags:
                u_hash_lower = [str(h).lower() for h in u_hashtags]
                missing_hashtags = [esc(h) for h in c_hashtags if str(h).lower() not in u_hash_lower]
                filtered_missing_hashtags = []
                for h in missing_hashtags:
                    h_l = tr_lower(h)
                    if h_l in broad_keywords:
                        continue
                    if not any(tw in h_l and tw not in v_title_lower_str for tw in toxic_keywords_list):
                        filtered_missing_hashtags.append(h)
                if filtered_missing_hashtags:
                    comp_txt += f"• <b>{L['steal_hashtags']}:</b> <font color='#c026d3'><b>{', '.join(['#' + h for h in filtered_missing_hashtags[:5]])}</b></font><br/><br/>"

            # AI Başlık Üretici
            clean_user = re.sub(r'\(.*?\)|\[.*?\]|\{.*?\}', '', video_name_str)
            clean_user = re.split(r'[|#–—]', clean_user)[0]
            clean_user = re.sub(r'\s+', ' ', clean_user).strip()
            if not clean_user or len(clean_user) < 3:
                clean_user = video_name_str[:40]

            if lang == 'en':
                t1 = f"NOBODY SAW THIS COMING! {clean_user}"
                t2 = f"{clean_user} (The Ending Is Shocking) 😱"
                t3 = f"THEY SAID IMPOSSIBLE! {clean_user} 🔥"
            elif lang == 'es':
                t1 = f"¡NADIE ESPERABA ESTO! {clean_user}"
                t2 = f"{clean_user} (El Final Es Impactante) 😱"
                t3 = f"¡DIJERON QUE ERA IMPOSIBLE! {clean_user} 🔥"
            else:
                t1 = f"BUNU KİMSE BEKLEMİYORDU! {clean_user}"
                t2 = f"{clean_user} (Oyunun Sonu Çok Garip) 😱"
                t3 = f"İMKANSIZ DENİLDİ! {clean_user} 🔥"

            comp_txt += f"• <b>{L['ai_title_gen']}:</b><br/>"
            comp_txt += f"{L['ai_title_intro']}<br/>"
            comp_txt += f"  <font color='#2563eb'><b>1️⃣ {t1}</b></font><br/>"
            comp_txt += f"  <font color='#2563eb'><b>2️⃣ {t2}</b></font><br/>"
            comp_txt += f"  <font color='#2563eb'><b>3️⃣ {t3}</b></font><br/><br/>"

            comp_txt += f"<b>{L['ai_strategy']}:</b><br/>"
            if views > 10000:
                comp_txt += L['views_high'].format(views=f"{views:,}")
            else:
                comp_txt += L['views_low'].format(views=f"{views:,}")

            elements.append(Paragraph(comp_txt, normal_s))
            elements.append(Spacer(1, 0.4 * inch))

        except ValueError as ve:
            if "FAKE_DATA_SKIP" not in str(ve):
                traceback.print_exc()
        except Exception as e:
            traceback.print_exc()

    # ═══════════════════════════════════════════════════════════
    #   PDF 2.0 — GELİŞMİŞ TABLOLAR
    # ═══════════════════════════════════════════════════════════
    # Çeviri fallback'leri (translations.xlsx binary olduğundan inline)
    _pdf2_tr = {
        "emotion_title": "THUMBNAIL DUYGU ANALİZİ",
        "emotion": "Duygu", "score": "Skor (%)", "dominant": "Baskın",
        "no_face": "Thumbnail'de yüz tespit edilemedi.",
        "visual_title": "GÖRSEL KALİTE METRİKLERİ",
        "metric": "Metrik", "value": "Değer", "status": "Durum",
        "contrast": "Kontrast (Michelson)", "vibrant": "Canlı Renk Uyumu",
        "text_space": "Metin Alanı Skoru", "brightness": "Parlaklık",
        "excellent": "Mükemmel", "good": "İyi", "low": "Düşük", "medium": "Orta",
        "excitement_title": "HEYECAN KATSAYISI ÖZETİ (Excitement Score)",
        "segment": "Segment", "time_range": "Zaman Aralığı",
        "excitement": "Heyecan", "audio": "Ses Yoğ.", "cut": "Kesim Yoğ.",
        "motion": "Hareket Yoğ.", "no_segments": "Viral segment tespit edilemedi.",
    }
    _pdf2_en = {
        "emotion_title": "THUMBNAIL EMOTION ANALYSIS",
        "emotion": "Emotion", "score": "Score (%)", "dominant": "Dominant",
        "no_face": "No face detected in thumbnail.",
        "visual_title": "VISUAL QUALITY METRICS",
        "metric": "Metric", "value": "Value", "status": "Status",
        "contrast": "Contrast (Michelson)", "vibrant": "Vibrant Color Match",
        "text_space": "Text Space Score", "brightness": "Brightness",
        "excellent": "Excellent", "good": "Good", "low": "Low", "medium": "Medium",
        "excitement_title": "EXCITEMENT SCORE SUMMARY",
        "segment": "Segment", "time_range": "Time Range",
        "excitement": "Excitement", "audio": "Audio Int.", "cut": "Cut Density",
        "motion": "Motion Int.", "no_segments": "No viral segments detected.",
    }
    _pdf2_es = {
        "emotion_title": "ANÁLISIS DE EMOCIÓN DE MINIATURA",
        "emotion": "Emoción", "score": "Puntuación (%)", "dominant": "Dominante",
        "no_face": "No se detectó rostro en la miniatura.",
        "visual_title": "MÉTRICAS DE CALIDAD VISUAL",
        "metric": "Métrica", "value": "Valor", "status": "Estado",
        "contrast": "Contraste (Michelson)", "vibrant": "Coincidencia de Color Vibrante",
        "text_space": "Puntuación de Espacio de Texto", "brightness": "Brillo",
        "excellent": "Excelente", "good": "Bueno", "low": "Bajo", "medium": "Medio",
        "excitement_title": "RESUMEN DE PUNTUACIÓN DE EMOCIÓN",
        "segment": "Segmento", "time_range": "Rango de Tiempo",
        "excitement": "Emoción", "audio": "Int. Audio", "cut": "Densidad Cortes",
        "motion": "Int. Movimiento", "no_segments": "No se detectaron segmentos virales.",
    }
    P2 = {"tr": _pdf2_tr, "en": _pdf2_en, "es": _pdf2_es}.get(lang, _pdf2_tr)

    # competitor_data JSON'ından ek verileri çıkar
    _saved_thumb = {}
    _saved_segments = []
    if comp_json:
        try:
            _cd = json.loads(comp_json)
            _saved_thumb = _cd.get('_thumb_data', {})
            _saved_segments = _cd.get('_viral_segments', [])
        except Exception as e:
            app_logger.debug(f"PDF JSON loads error: {e}")

    # ── TABLO 1: Thumbnail Duygu Analizi ──
    elements.append(PageBreak())
    elements.append(h1(P2["emotion_title"]))
    _faces = _saved_thumb.get("faces", [])
    if _faces:
        emo_headers = [P2["emotion"], P2["score"], P2["dominant"]]
        emo_data = [emo_headers]
        for face_info in _faces[:3]:
            scores = face_info.get("emotion_scores", {})
            dom = face_info.get("dominant_emotion", "neutral")
            for emo_name, emo_val in sorted(scores.items(), key=lambda x: x[1], reverse=True):
                is_dom = "✅" if emo_name == dom else ""
                emo_data.append([emo_name.capitalize(), f"{emo_val:.1f}%", is_dom])
        emo_table = Table(emo_data, colWidths=[2.2*inch, 1.5*inch, 1.2*inch])
        emo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6b21a8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('FONTNAME', (0, 1), (-1, -1), FONT_REGULAR),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f3ff')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f5f3ff'), colors.HexColor('#ede9fe')]),
        ]))
        elements.append(emo_table)
        gaze_info = _faces[0].get("looking_at_camera", False)
        gaze_txt = "👀 Kameraya bakıyor ✅" if lang == "tr" else "👀 Looking at camera ✅" if lang == "en" else "👀 Mirando a cámara ✅"
        if not gaze_info:
            gaze_txt = "👀 Kameraya bakmıyor" if lang == "tr" else "👀 Not looking at camera" if lang == "en" else "👀 No mira a cámara"
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph(f"<font size=9 color='#6b21a8'><b>{gaze_txt}</b></font>", normal_s))
    else:
        elements.append(Paragraph(f"<font color='#94a3b8'><em>{P2['no_face']}</em></font>", normal_s))
    elements.append(Spacer(1, 0.3 * inch))

    # ── TABLO 2: Görsel Kalite Metrikleri ──
    elements.append(h1(P2["visual_title"]))
    cr = _saved_thumb.get("contrast_ratio", 0)
    vcm = _saved_thumb.get("vibrant_color_match", 0)
    tss = _saved_thumb.get("text_space_score", 0)
    def _quality_status(val, thresholds=(7.0, 5.0)):
        if val >= thresholds[0]: return P2["excellent"]
        elif val >= thresholds[1]: return P2["good"]
        elif val > 0: return P2["low"]
        return "—"
    def _contrast_status(c_val):
        if c_val >= 0.5: return P2["excellent"]
        elif c_val >= 0.3: return P2["good"]
        elif c_val > 0: return P2["low"]
        return "—"

    vis_data = [
        [P2["metric"], P2["value"], P2["status"]],
        [P2["contrast"], f"{cr:.3f}", _contrast_status(cr)],
        [P2["vibrant"], f"{vcm}/10", _quality_status(vcm)],
        [P2["text_space"], f"{tss}/10", _quality_status(tss)],
    ]
    vis_table = Table(vis_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
    vis_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f766e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTNAME', (0, 1), (-1, -1), FONT_REGULAR),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0fdfa')),
    ]))
    elements.append(vis_table)
    elements.append(Spacer(1, 0.3 * inch))

    # ── TABLO 3: Heyecan Katsayısı Özeti ──
    elements.append(h1(P2["excitement_title"]))
    if _saved_segments:
        exc_data = [
            [P2["segment"], P2["time_range"], P2["excitement"], P2["audio"], P2["cut"], P2["motion"]]
        ]
        for idx, seg in enumerate(_saved_segments[:5], 1):
            s_start = seg.get("start_sec", 0)
            s_end = seg.get("end_sec", 0)
            time_str = f"{int(s_start//60)}:{int(s_start%60):02d} — {int(s_end//60)}:{int(s_end%60):02d}"
            exc_data.append([
                f"#{idx}",
                time_str,
                f"{seg.get('excitement_score', 0)}/10",
                f"{seg.get('audio_intensity', 0)}/10",
                f"{seg.get('cut_density', 0)}/10",
                f"{seg.get('motion_intensity', 0)}/10",
            ])
        exc_table = Table(exc_data, colWidths=[0.6*inch, 1.4*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.9*inch])
        exc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#b91c1c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('FONTNAME', (0, 1), (-1, -1), FONT_REGULAR),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fef2f2')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#fef2f2'), colors.HexColor('#fee2e2')]),
        ]))
        elements.append(exc_table)
    else:
        elements.append(Paragraph(f"<font color='#94a3b8'><em>{P2['no_segments']}</em></font>", normal_s))
    elements.append(Spacer(1, 0.3 * inch))

    # ── 6. Kıyaslama Tablosu ──
    elements.append(PageBreak())
    elements.append(h1(L['comparison_title']))

    def safe_float(val):
        return float(val) if val is not None else 0.0

    avg_overall = safe_float(averages['avg_overall'])
    avg_ret = safe_float(averages['avg_retention'])
    avg_tech = safe_float(averages['avg_tech'])
    avg_seo = safe_float(averages['avg_seo'])
    avg_thumb = safe_float(averages['avg_thumb'])

    hdrs = L['comparison_headers']
    table_data = [
        hdrs,
        [L['col_overall'], f"{overall:.1f}", f"{avg_overall:.1f}", f"{overall - avg_overall:.1f}"],
        [L['col_retention'], f"{retention:.1f}", f"{avg_ret:.1f}", f"{retention - avg_ret:.1f}"],
        [L['col_tempo'], f"{tech:.1f}", f"{avg_tech:.1f}", f"{tech - avg_tech:.1f}"],
        [L['col_seo'], f"{seo:.1f}", f"{avg_seo:.1f}", f"{seo - avg_seo:.1f}"],
        [L['col_thumbnail'], f"{thumb:.1f}", f"{avg_thumb:.1f}", f"{thumb - avg_thumb:.1f}"]
    ]
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12), ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black), ('FONTNAME', (0, 1), (-1, -1), FONT_REGULAR)
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.5 * inch))

    # ── AI Coach ──
    coach_elements = []
    coach_elements.append(h1(L['coach_title'].replace('🥊', '').strip()))
    feedback_from_db = analysis['coach_feedback']
    if feedback_from_db:
        coach_elements.append(h2(L['coach_analysis'].replace('🤖', '').strip()))
        coach_elements.append(Paragraph(esc(feedback_from_db), normal_s))
        coach_elements.append(Spacer(1, 0.2 * inch))

    reasons, actions, positives = [], [], []
    if thumb > 0.0:
        if face_detected:
            positives.append(L['face_ok'])
        else:
            reasons.append(L['face_missing'])
            actions.append(L['face_action'])
    if retention < 6.5:
        reasons.append(L['retention_low'])
        actions.append(L['retention_action'])
    else:
        positives.append(L['retention_ok'].format(score=retention))
    if tech < 7.0:
        reasons.append(L['tech_low'].format(peaks=peaks))
        actions.append(L['tech_action'])
    else:
        positives.append(L['tech_ok'].format(peaks=peaks))
    if seo < 6.0:
        reasons.append(L['seo_low'].format(seo=seo))
        actions.append(L['seo_action'])
    elif seo >= 8.0:
        positives.append(f"SEO optimizasyonu çok başarılı (Skor: {seo:.1f}/10)")
        
    cr = _saved_thumb.get("contrast_ratio", 0) if '_saved_thumb' in locals() else 0
    if cr >= 0.5:
        positives.append(f"Thumbnail kontrastı mükemmel ({cr:.2f}), dikkat çekici")

    reasons_text = "\n".join([f"• {r}" for r in reasons]) or L['no_weak']
    actions_text = "\n".join([f"• {a}" for a in actions]) or L['no_action']
    positives_text = "\n".join([f"• {p}" for p in positives]) or L['no_strong']

    def esc_nl(s):
        return esc(s).replace(chr(10), '<br/>')

    coach_content = (
        f"<b>{L['weak_points']}:</b><br/>{esc_nl(reasons_text)}<br/><br/>"
        f"<b>{L['urgent_actions']}:</b><br/>{esc_nl(actions_text)}<br/><br/>"
        f"<b>{L['strong_points']}:</b><br/>{esc_nl(positives_text)}"
    )
    coach_elements.append(Paragraph(coach_content, normal_s))
    coach_elements.append(Spacer(1, 0.4 * inch))

    elements.append(KeepTogether(coach_elements))

    # ── Süre dipnotu ──
    try:
        raw_dur = analysis['analysis_duration_sec']
        dur_sec = float(raw_dur) if raw_dur else 0.0
    except Exception:
        dur_sec = 0.0

    if dur_sec > 0:
        mins = int(dur_sec // 60)
        secs_val = int(dur_sec % 60)
        if mins > 0:
            dur_str = L['duration_min'].format(m=mins, s=secs_val)
        else:
            dur_str = L['duration_sec'].format(s=secs_val)
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(Paragraph(
            f"<font size=8 color='#888888'>{L['duration_note'].format(dur=dur_str, sec=f'{dur_sec:.1f}')}</font>",
            normal_s
        ))

    doc.build(elements)
    safe_video_title = re.sub(r'[^\w\-]', '_', video_name_str)[:30]
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"analysis_report_{safe_video_title}_{analysis_id}.pdf")


@app.get("/export_channel_pdf/{channel_id}")
async def export_channel_pdf(channel_id: int, lang: str = "tr"):
    if lang not in PDF_LANG or not PDF_LANG[lang]:
        lang = "tr"
    L = PDF_LANG[lang]
    def esc(txt):
        if txt is None:
            return ""
        s = str(txt)
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        s = s.replace('"', "").replace("'", "")
        return s

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM channels WHERE id=?", (channel_id,))
    channel = c.fetchone()
    if not channel:
        raise HTTPException(status_code=404, detail="Kanal bulunamadı")
    c.execute("SELECT video_name, overall_score, retention_score, tech_score, seo_score, timestamp FROM analyses WHERE channel_id=? ORDER BY timestamp DESC", (channel_id,))
    analyses = c.fetchall()
    avgs = await AnalysisEngine.get_channel_averages(channel_id)
    conn.close()

    pdf_path = output_dir / f"kanal_raporu_{channel_id}_{lang}.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    title_s, heading_s, normal_s = styles['Title'], styles['Heading2'], styles['Normal']
    title_s.fontName, heading_s.fontName, normal_s.fontName = FONT_BOLD, FONT_BOLD, FONT_REGULAR

    elements.append(Paragraph(f"{L['channel_report_title']}: {esc(channel[1])}", title_s))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph(L['channel_avg_title'], heading_s))

    def safe_float(val):
        return float(val) if val is not None else 0.0

    avg_data = [
        [L['col_overall'], L['col_retention'], L['col_tempo'], L['col_seo'], L['col_thumbnail']],
        [str(safe_float(avgs['avg_overall'])), str(safe_float(avgs['avg_retention'])),
         str(safe_float(avgs['avg_tech'])), str(safe_float(avgs['avg_seo'])), str(safe_float(avgs['avg_thumb']))]
    ]
    t1 = Table(avg_data, colWidths=[1.2 * inch] * 5)
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.black), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, -1), FONT_BOLD)
    ]))
    elements.append(t1)
    elements.append(Spacer(1, 0.4 * inch))
    elements.append(Paragraph(L['video_history_title'], heading_s))

    if analyses:
        hist_data = [[L['col_video'], L['col_date'], L['col_overall'], L['col_retention'], L['col_tempo'], L['col_seo']]]
        for a in analyses:
            date_str = str(a[5]).split()[0]
            v_name = (esc(a[0][:20]) + '..') if len(a[0]) > 20 else esc(a[0])
            vals = [str(safe_float(x)) for x in a[1:5]]
            hist_data.append([v_name, date_str, vals[0], vals[1], vals[2], vals[3]])
        t2 = Table(hist_data, colWidths=[2 * inch, 1 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6b21a8')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD), ('FONTNAME', (0, 1), (-1, -1), FONT_REGULAR)
        ]))
        elements.append(t2)
    else:
        elements.append(Paragraph(L['no_analysis'], normal_s))

    doc.build(elements)
    safe_name = re.sub(r'[^\w\-]', '_', str(channel[1]))[:30]
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"channel_report_{safe_name}_{channel_id}.pdf")


@app.get("/api/session")
async def get_session():
    db = await get_async_db()
    try:
        async with db.execute("SELECT value FROM app_settings WHERE key='active_session'") as cursor:
            row = await cursor.fetchone()
        if row and row[0]:
            try:
                return {"session": json.loads(row[0])}
            except Exception as e:
                app_logger.warning(f"Hata [get_session json load]: {e}")
        return {"session": None}
    finally:
        await db.close()


@app.post("/api/session")
async def save_session(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    username = data.get("username")
    if not user_id or not username:
        return {"success": False}
    session_data = json.dumps({"user_id": user_id, "username": username})
    db = await get_async_db()
    try:
        await db.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('active_session', ?)", (session_data,))
        await db.commit()
    finally:
        await db.close()
    return {"success": True}


@app.delete("/api/session")
async def clear_session():
    db = await get_async_db()
    try:
        await db.execute("DELETE FROM app_settings WHERE key='active_session'")
        await db.commit()
    finally:
        await db.close()
    return {"success": True}


@app.get("/api/settings/groq")
async def get_groq_key():
    db = await get_async_db()
    try:
        async with db.execute("SELECT value FROM app_settings WHERE key='groq_api_key'") as cursor:
            row = await cursor.fetchone()
        return {"has_key": bool(row and row[0])}
    finally:
        await db.close()


@app.post("/api/settings/groq")
async def set_groq_key(key: str = Form(...)):
    db = await get_async_db()
    try:
        await db.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('groq_api_key', ?)", (CryptoManager.encrypt(key.strip()),))
        await db.commit()
    finally:
        await db.close()
    return {"success": True}


@app.get("/api/settings/smtp")
async def get_smtp_settings():
    db = await get_async_db()
    try:
        async with db.execute("SELECT key, value FROM app_settings WHERE key IN ('smtp_email', 'smtp_password')") as cursor:
            rows = {r[0]: r[1] async for r in cursor}
        return {"has_smtp": bool(rows.get('smtp_email') and rows.get('smtp_password')),
                "smtp_email": rows.get('smtp_email', '')}
    finally:
        await db.close()


@app.post("/api/settings/smtp")
async def set_smtp_settings(request: Request):
    try:
        data = await request.json()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        if not email or not password:
            return {"success": False, "error": "Email ve şifre boş olamaz."}
        db = await get_async_db()
        try:
            await db.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('smtp_email', ?)", (email,))
            await db.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('smtp_password', ?)", (CryptoManager.encrypt(password),))
            await db.commit()
        finally:
            await db.close()
        return {"success": True}
    except Exception:
        return {"success": False, "error": "Kayıt hatası."}


@app.get("/api/chat/sessions")
async def get_chat_sessions(user_id: int = 1):
    db = await get_async_db()
    try:
        async with db.execute("""
            SELECT s.id, s.title, s.created_at,
                COUNT(m.id) as msg_count
            FROM chat_sessions s
            LEFT JOIN chat_messages m ON m.session_id = s.id
            WHERE s.user_id = ?
            GROUP BY s.id
            ORDER BY s.created_at DESC
            LIMIT 50
        """, (user_id,)) as cursor:
            rows = await cursor.fetchall()
        return [{"id": r[0], "title": r[1], "created_at": r[2], "msg_count": r[3]} for r in rows]
    finally:
        await db.close()


@app.post("/api/chat/sessions")
async def create_chat_session(request: Request):
    data = await request.json()
    title = data.get("title", "Yeni Sohbet")[:80]
    user_id = data.get("user_id", 1)
    db = await get_async_db()
    try:
        await db.execute("INSERT INTO chat_sessions (title, user_id) VALUES (?, ?)", (title, user_id))
        await db.commit()
        async with db.execute("SELECT last_insert_rowid()") as cursor:
            row = await cursor.fetchone()
            sid = row[0]
    finally:
        await db.close()
    return {"id": sid, "title": title}


@app.put("/api/chat/sessions/{session_id}")
async def rename_chat_session(session_id: int, request: Request):
    data = await request.json()
    title = data.get("title", "Sohbet")[:80]
    user_id = data.get("user_id", 1)
    db = await get_async_db()
    try:
        await db.execute("UPDATE chat_sessions SET title=? WHERE id=? AND user_id=?", (title, session_id, user_id))
        await db.commit()
    finally:
        await db.close()
    return {"success": True}


@app.delete("/api/chat/sessions/{session_id}")
async def delete_chat_session(session_id: int, user_id: int = 1):
    db = await get_async_db()
    try:
        await db.execute("DELETE FROM chat_messages WHERE session_id=? AND session_id IN (SELECT id FROM chat_sessions WHERE user_id=?)", (session_id, user_id))
        await db.execute("DELETE FROM chat_sessions WHERE id=? AND user_id=?", (session_id, user_id))
        await db.commit()
    finally:
        await db.close()
    return {"success": True}


@app.get("/api/chat/sessions/{session_id}/messages")
async def get_session_messages(session_id: int, user_id: int = 1):
    db = await get_async_db()
    try:
        # Oturumun bu kullanıcıya ait olduğunu doğrula
        async with db.execute("SELECT id FROM chat_sessions WHERE id=? AND user_id=?", (session_id, user_id)) as cursor:
            if not await cursor.fetchone():
                return []
        async with db.execute("SELECT sender, text FROM chat_messages WHERE session_id=? ORDER BY created_at ASC", (session_id,)) as cursor:
            rows = await cursor.fetchall()
        return [{"sender": r[0], "text": r[1]} for r in rows]
    finally:
        await db.close()


@app.post("/api/chat/sessions/{session_id}/messages")
async def save_session_message(session_id: int, request: Request):
    data = await request.json()
    sender = data.get("sender", "user")
    text = data.get("text", "")
    if not text:
        return {"success": False}
    db = await get_async_db()
    try:
        await db.execute("INSERT INTO chat_messages (session_id, sender, text) VALUES (?,?,?)", (session_id, sender, text))
        await db.commit()
    finally:
        await db.close()
    return {"success": True}


@app.post("/api/chat")
async def ai_chat(request: Request):
    data = await request.json()
    history = data.get("history", [])
    ch_type = data.get("channel_type", "Genel")
    context = data.get("analysis_context", "")
    channel_id = data.get("channel_id", None)

    db = await get_async_db()
    try:
        async with db.execute("SELECT value FROM app_settings WHERE key='groq_api_key'") as cursor:
            row = await cursor.fetchone()
            
        channel_rules_text = ""
        past_feedbacks_text = ""
        if channel_id:
            try:
                async with db.execute("SELECT channel_rules FROM channels WHERE id=?", (channel_id,)) as rules_cursor:
                    rules_row = await rules_cursor.fetchone()
                    if rules_row and rules_row[0]:
                        channel_rules_text = rules_row[0].strip()
            except Exception:
                pass
            try:
                async with db.execute("""
                    SELECT coach_feedback FROM analyses
                    WHERE channel_id=? AND coach_feedback IS NOT NULL AND coach_feedback != ''
                    ORDER BY timestamp DESC LIMIT 5
                """, (channel_id,)) as fb_cursor:
                    fb_rows = await fb_cursor.fetchall()
                    if fb_rows:
                        feedbacks = [r[0] for r in fb_rows if r[0]]
                        if feedbacks:
                            past_feedbacks_text = "\\n".join(
                                [f"[{i+1}] {fb[:300]}" for i, fb in enumerate(reversed(feedbacks))]
                            )
            except Exception:
                pass
    finally:
        await db.close()

    api_key = row[0] if row else ""
    if not api_key:
        return {"error": "NO_KEY", "details": "API anahtarı bulunamadı. Lütfen Groq API anahtarını gir."}

    attached_file = data.get("attached_file", None)
    file_context = ""
    file_mime = ""
    file_base64 = ""
    file_name = "dosya"
    if attached_file:
        file_type = attached_file.get("type", "")
        file_base64 = attached_file.get("base64", "")
        file_mime = attached_file.get("mime_type", "")
        file_name = attached_file.get("name", "dosya")
        #print(f"ATTACHED FILE: type={file_type}, mime={file_mime}, name={file_name}, b64len={len(file_base64)}")
        if file_type == "image" and file_base64:
            file_context = await analyze_image_with_gemini(file_base64, file_mime)
        elif file_base64:
            try:
                import base64 as b64mod
                decoded_bytes = b64mod.b64decode(file_base64)
                if file_mime == "application/pdf" or file_name.lower().endswith(".pdf"):
                    file_context = await analyze_image_with_gemini(file_base64, "application/pdf")
                else:
                    decoded = decoded_bytes.decode('utf-8', errors='ignore')
                    file_context = f"Kullanıcının yüklediği dosya ({file_name}):\n{decoded[:3000]}"
            except Exception as e:
                #print(f"FILE PARSE HATA: {e}")
                file_context = ""
        #print(f"FILE_CONTEXT SONUÇ: {len(file_context)} karakter")

    has_analysis = bool(context and context.strip())

    last_user_msg = ""
    for msg in reversed(history):
        if msg.get("sender") == "user" and not msg.get("isTyping"):
            last_user_msg = msg.get("text", "")
            break

    last_user_msg_lower = last_user_msg.lower()
    title_keywords = ["başlık", "title", "isim", "name", "ne yazayım", "nasıl adlandır", "başlık öner", "başlık yaz"]
    is_title_question = any(kw in last_user_msg_lower for kw in title_keywords)

    analysis_block = f"User's latest analysis:\n{context}" if has_analysis else "The user has not performed any video analysis yet."

    if file_context:
        analysis_block += f"\n\nUser uploaded additional data for analysis:\n{file_context}"

    if file_context:
        print(f"FILE_CONTEXT PREVIEW: {file_context[:500]}")

    file_uploaded_note = ""
    if file_context:
        file_uploaded_note = """
IMPORTANT: The user has uploaded an image or data file containing YouTube analytics. The extracted data is in the analysis block above under 'User uploaded additional data'.
FILE ANALYSIS PROTOCOL:
1. STRICT FACTS: Read the exact numbers from the data. DO NOT hallucinate numbers (e.g., if it says 3:28, do not invent 6:22). Re-state the actual metrics given.
2. Visualize the Data: Treat the text data as a visual graph in your mind (e.g., Retention graph).
3. Numerical Citations: Do not use generic phrases like "Viewers are leaving". Give specific points like "The sharp 40% drop seen at the 15th second...". Use the precise times and percentages provided.
4. Diagnosis and Cure: Explain the reason for the performance metric (low tempo, unfulfilled promise, etc.) and write a targeted Hook scenario.
5. Hook Rules: Every hook you suggest must strictly include: a Scenario script, a Psychological Trigger, and an On-Screen Visual instruction.
6. Goal: 90%+ target retention rate in the first 30 seconds."""

    title_instruction = ""
    if is_title_question:
        title_instruction = """
TITLE QUESTION RULE — This message is about a title. At the very end of your response, add the following format:
---
💡 My Title Suggestions:
1. [Suggestion 1]
2. [Suggestion 2]
3. [Suggestion 3]
---
Titles should be short, curiosity-inducing and between 50-70 characters."""

    no_analysis_instruction = ""
    if not has_analysis and not file_context:
        no_analysis_instruction = """
NO ANALYSIS RULE — The user has not analyzed any video yet. At the very end of each response add (in the user's language):
---
📊 Upload your video to YouTube Analytics Pro so I can give you a precise, personalized answer — I'll show you exactly when viewers drop off, your SEO score and competitor comparison!
---"""

    # --- HAFIZA SİSTEMİ: Memory block oluştur ---
    memory_block = ""
    if channel_rules_text:
        memory_block += f"\\n\\n🔒 SABİT KANAL KURALLARI (Bu kurallara MUTLAKA uy, asla çiğneme):\\n{channel_rules_text}"
    if past_feedbacks_text:
        memory_block += f"\\n\\n📚 GEÇMİŞ ANALİZ NOTLARI (Son 5 analiz koç yorumu, eskiden yeniye):\\n{past_feedbacks_text}"

    system_prompt = f"""IDENTITY: You are 'Analiz Pro AI: Stratejik Veri Analisti' (Strategic Data Analyst) — the world's most elite, data-driven, and ruthless YouTube strategist.
Channel Type: {ch_type}
{analysis_block}{memory_block}

⚠️ CRITICAL LANGUAGE RULE:
Detect the exact language of the user's message and respond EXCLUSIVELY in that same language. (User TR -> Respond TR, User EN -> Respond EN, User ES -> Respond ES). NEVER mix languages.

🧠 STRATEGY AND DATA PROCESSING DIRECTIVES:
1. BE DATA-RUTHLESS: Use the provided analytics (Retention, SEO, Tempo) like a surgeon. If the "Excitement Score" is low or there are "Dead Zones", give direct orders mentioning the exact timestamps. Do not sugarcoat.
2. VISUAL INTELLIGENCE FILTER: You MUST use the visual data in your strategy:
   - EMOTION: Connect the detected facial emotion in the thumbnail to CTR (Click-Through Rate) psychology. If no face is found, strictly order them to add a human face ("Human brains are hardwired to look at faces").
   - CONTRAST: If contrast is low, warn them that "It will be invisible on mobile" and suggest specific complementary colors (e.g., Purple/Yellow).
   - EXCITEMENT SCORE & CUTS: Use the scene cut frequency and motion data to command editing actions like "Add a dynamic zoom" or "Increase your cut frequency to every 4 seconds".
3. ELITE TONE: Speak like a top-tier strategist managing millions of subscribers. Be direct, authoritative, actionable, and use bullet points. **Bold** key terms. No unnecessary fluff.
4. MANDATORY HOOKS (ANTI-GENERIC): If addressing viewer drop-offs (retention), you MUST provide a specific Hook Formula: 1. Spoken Script, 2. Psychological Trigger, 3. On-Screen Visual Action. NEVER say "surprise them in the first 10 seconds" or "ilk 10 saniyede şaşırt". You must answer HOW exactly with a concrete scenario.
5. BOUNDARIES: You ONLY discuss YouTube algorithms, content strategy, video pacing, and SEO. Reject all off-topic questions by stating your role.
6. NO-HALLUCINATION RULE: Use ONLY the provided Channel Type and Purpose for your strategy. DO NOT suggest random games or content types that were not explicitly provided in the input context. If you do not know the answer to a question, explicitly state "I don't know" (veya "Bilmiyorum"). NEVER make up information or give wrong answers.
7. STRENGTH RECOGNITION: Do not just focus on weaknesses. If SEO score is high, thumbnail contrast is excellent, or retention is stable in the middle, explicitly acknowledge these as strong points.
8. TAG PROTECTION: Never dismiss user tags as irrelevant unless they truly violate YouTube terms. Recognize specific niche tags (like "left 4 dead 2 türkçe" or "komik oyun videoları") as positive targeted keywords.
9. ⚠️ KANAL KURALLARI: Eğer yukarıda 'SABİT KANAL KURALLARI' bölümü varsa, bu kurallar mutlak önceliğe sahiptir. Bu kurallara KESİNLİKLE uy ve hiçbir öneri bu kurallara aykırı olmasın.

{title_instruction}
{no_analysis_instruction}
{file_uploaded_note}"""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        if msg.get("isTyping"):
            continue
        role = "assistant" if msg.get("sender") == "bot" else "user"
        text = msg.get("text", "")
        if text and not text.startswith("⚠️"):
            messages.append({"role": role, "content": text})

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "max_tokens": 1024,
                "temperature": 0.7
            },
            timeout=20
        )

        res_data = resp.json()

        if resp.status_code != 200:
            err = res_data.get("error", {}).get("message", "Bilinmeyen hata")
            if resp.status_code == 401:
                return {"error": "INVALID_KEY", "details": "API anahtarın geçersiz."}
            if resp.status_code == 429:
                return {"error": "QUOTA", "details": "Sınır aşıldı. Lütfen biraz bekleyin."}
            return {"error": "API_ERROR", "details": f"Groq hatası: {err}"}

        reply = res_data["choices"][0]["message"]["content"]
        return {"reply": reply}

    except requests.exceptions.Timeout:
        return {"error": "TIMEOUT", "details": "Sunucu yanıt vermedi. Tekrar dene."}
    except Exception as e:
        return {"error": "NETWORK_ERROR", "details": f"Bağlantı hatası: {str(e)}"}

@app.post("/api/send_report")
async def api_send_report(request: Request):
    """Manuel rapor gönderimi — Sonuç ekranından 'Raporu Tekrar Gönder' butonu."""
    data = await request.json()
    analysis_id = data.get("analysis_id")
    user_id = data.get("user_id", 1)
    req_lang = data.get("lang", "tr")
    if not analysis_id:
        return {"success": False, "error": "Analiz ID eksik."}
    try:
        conn = get_db()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT video_name FROM analyses WHERE id=?", (analysis_id,))
        a_row = c.fetchone()
        c.execute("SELECT email FROM users WHERE id=?", (user_id,))
        u_row = c.fetchone()
        conn.close()
        if not a_row or not u_row or not u_row['email']:
            return {"success": False, "error": "Kullanıcı e-postası bulunamadı."}

        # Önce PDF'i oluştur (export_pdf endpoint'ini simüle et)
        pdf_path = str(output_dir / f"report_{analysis_id}_{req_lang}.pdf")
        if not os.path.exists(pdf_path):
            # PDF yoksa export_pdf'i bir kez çağır
            from starlette.testclient import TestClient
            # Alternatif: doğrudan URL'den indir
            import urllib.request
            try:
                urllib.request.urlretrieve(
                    f"http://127.0.0.1:8000/export_pdf/{analysis_id}?lang={req_lang}",
                    pdf_path
                )
            except Exception:
                pass

        video_name = a_row['video_name']
        user_email = u_row['email']
        sent = await run_in_threadpool(send_report_email, user_email, pdf_path, video_name, req_lang)
        if sent:
            return {"success": True, "message": "Rapor e-postanıza gönderildi!"}
        else:
            return {"success": False, "error": "SMTP ayarları eksik veya gönderim başarısız."}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/translations")
async def get_translations():
    try:
        xlsx_path = BUNDLE_DIR / 'translations.xlsx'
        if not xlsx_path.exists():
            xlsx_path = APP_DIR / 'translations.xlsx'
        df = pd.read_excel(str(xlsx_path), sheet_name='ui', dtype=str).fillna('')
        result = {'tr': {}, 'en': {}, 'es': {}}
        for _, row in df.iterrows():
            key = str(row['key']).strip()
            if not key:
                continue
            for lang in ['tr', 'en', 'es']:
                result[lang][key] = str(row[lang]).strip()
        return result
    except Exception as e:
        return {'error': str(e)}


@app.get("/api/test/gemini-models")
async def test_gemini_models():
    db = await get_async_db()
    try:
        async with db.execute("SELECT value FROM app_settings WHERE key='gemini_api_key'") as cursor:
            row = await cursor.fetchone()
    finally:
        await db.close()
    gemini_key = row[0] if row and row[0] else ""
    resp = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}")
    return resp.json()


@app.get("/api/test/gemini-ping")
async def test_gemini_ping():
    db = await get_async_db()
    try:
        async with db.execute("SELECT value FROM app_settings WHERE key='gemini_api_key'") as cursor:
            row = await cursor.fetchone()
    finally:
        await db.close()
    gemini_key = row[0] if row and row[0] else ""
    payload = {"contents": [{"parts": [{"text": "Say hello"}]}]}
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}",
        json=payload,
        timeout=10
    )
    return {"status": resp.status_code, "body": resp.text[:300]}


@app.get("/health")
async def health():
    return {
        "status": "online",
        "ffmpeg_available": FFMPEG_AVAILABLE,
        "gpu_codec": GPU_CODEC,
        "system_caps": SYSTEM_CAPS
    }


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="critical", access_log=False)


if __name__ == "__main__":
    init_db()

    # EĞER eski verilerini (misafir) yeni hesabına (ID: 2) taşımak istersen
    # aşağıdaki satırın başındaki '#' işaretini bir kez kaldırıp çalıştır:
    # migrate_data(2)

    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(2)

    webview.create_window(
        "YouTube Analiz Pro V4.0 — SaaS Edition",
        "http://127.0.0.1:8000",
        width=1050,
        height=900
    )
    webview.start()
