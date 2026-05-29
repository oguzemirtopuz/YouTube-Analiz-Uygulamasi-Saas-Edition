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

# ─── Crossroads: EXE vs development ───────────────────── ──────────────────────
if getattr(sys, 'frozen', False):
    _APP_DIR = Path(os.path.dirname(sys.executable)).resolve()
else:
    # This file is located at app/services/security.py; project root 2 levels up
    _APP_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))).resolve()

_logger = logging.getLogger("yt_analiz.security")


# ─── Special Exception ────────────────────────────────── ───────────────────────────────────

class CryptoDecryptionError(RuntimeError):
    """Şifreli veri çözülemediğinde fırlatılır.

    Fail-Fast (Aşama 1) kuralı: Sahte veri üretmek YASAKTIR.
    Bu exception'u yakalayan endpoint'ler dürüstçe HTTPException dönmelidir.

    Olası nedenler:
      - .secret.key dosyası değiştirilmiş veya silinmiş.
      - Veritabanı başka bir makineden kopyalanmış (farklı key).
      - Veri bozulmuş (bit rot, doğrudan DB edit vb.).
    """
    pass


# ─── CryptoManager ────────────────────────────── ──────────────────────────────

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
        """Şifreli metni çözer.
        
        STRES TESTİ FIX: Anahtar kaybolursa veya bozulursa artık sessizce
        boş veri döndermüyor. Davranış şöyle:
          - InvalidToken (anahtar değişmiş / veri bozuk)  → WARNING log + "" döner
          - .secret.key dosyası yoksa get_fernet() yeni key yazar (normal akış)
          - Eski şifrelenmemiş veri (kısa, Fernet token formatı değil) → uyumluluk için orijinal text döner
        """
        if not text:
            return text
        try:
            return cls.get_fernet().decrypt(text.encode()).decode()
        except Exception as e:
            from cryptography.fernet import InvalidToken
            if isinstance(e, InvalidToken):
                # The key has changed or data has been corrupted: this is a SECURITY INCIDENT.
                # According to the Phase 1 (Fail-Fast) rule: It is PROHIBITED to return fake data/empty string.
                _logger.error(
                    "[CryptoManager] KRİTİK HATA: decrypt() InvalidToken hatası. "
                    "'.secret.key' dosyası değişmiş veya veri bozulmuş olabilir. "
                    "Etkilenen veri uzunluğu: %d karakter. CryptoDecryptionError fırlatılıyor.",
                    len(text)
                )
                raise CryptoDecryptionError("Şifreleme anahtarı bozuk veya veri geçersiz. Veriler okunamadı.")
            # Legacy unencrypted data (backwards compatibility)
            return text


# ─── Password transactions ──────────────────────────── ─────────────────────────────

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


# ─── Email verification code generator ───────────────────── ─────────────────────

def generate_verification_code() -> str:
    """6 haneli kriptografik olarak güvenli doğrulama kodu üretir."""
    return str(secrets.randbelow(900000) + 100000)
