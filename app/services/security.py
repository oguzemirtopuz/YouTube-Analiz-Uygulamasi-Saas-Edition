"""
app/services/security.py
─────────────────────────
Güvenlik katmanı — server.pyw'dan ayrıştırıldı (FAZ 2.1 Refactor).

İçerik:
  • CryptoManager      : Fernet simetrik şifreleme (API key, SMTP şifre)
  • hash_password      : PBKDF2-HMAC-SHA256 şifre hash'leme
  • verify_password    : Sabit-zaman karşılaştırmalı hash doğrulama
  • generate_verification_code : 6 haneli e-posta doğrulama kodu üreteci
"""

import os
import sys
import hashlib
import secrets
import random
import logging
from pathlib import Path
from cryptography.fernet import Fernet

# ─── Yol ayrımı: EXE vs geliştirme ───────────────────────────────────────────
if getattr(sys, 'frozen', False):
    _APP_DIR = Path(os.path.dirname(sys.executable)).resolve()
else:
    # Bu dosya  app/services/security.py  konumunda; proje kökü 2 seviye üstte
    _APP_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))).resolve()

_logger = logging.getLogger("yt_analiz.security")


# ─── CryptoManager ────────────────────────────────────────────────────────────

class CryptoManager:
    """Fernet simetrik şifreleme ile hassas verileri (API key, SMTP şifre) korur.
    .secret.key dosyası APP_DIR altında tutulur ve asla paylaşılmamalıdır.
    Eski şifrelenmemiş verileri bozmadan okuyabilir (geriye dönük uyumluluk).
    """
    KEY_FILE = _APP_DIR / ".secret.key"
    _fernet = None

    @classmethod
    def get_fernet(cls):
        if cls._fernet is None:
            if not cls.KEY_FILE.exists():
                with open(cls.KEY_FILE, "wb") as f:
                    f.write(Fernet.generate_key())
            with open(cls.KEY_FILE, "rb") as f:
                key = f.read()
            cls._fernet = Fernet(key)
        return cls._fernet

    @classmethod
    def encrypt(cls, text: str) -> str:
        """Metni şifreler. Boş string gelirse olduğu gibi döndürür."""
        if not text:
            return text
        return cls.get_fernet().encrypt(text.encode()).decode()

    @classmethod
    def decrypt(cls, text: str) -> str:
        """Şifreli metni çözer. Çözme başarısız olursa orijinal metni döndürür
        (eski şifrelenmemiş veriler için geriye dönük uyumluluk)."""
        if not text:
            return text
        try:
            return cls.get_fernet().decrypt(text.encode()).decode()
        except Exception:
            return text  # Geriye dönük uyumluluk: eski şifrelenmemiş veri


# ─── Şifre işlemleri ─────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 260000)
    return f"{salt}:{dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, dk_hex = stored_hash.split(':', 1)
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 260000)
        return secrets.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False


# ─── E-posta doğrulama kodu üreteci ──────────────────────────────────────────

def generate_verification_code() -> str:
    return str(random.randint(100000, 999999))
