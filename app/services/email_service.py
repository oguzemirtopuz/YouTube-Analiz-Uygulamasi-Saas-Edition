"""
app/services/email_service.py
──────────────────────────────
E-posta servisi — server.pyw'dan ayrıştırıldı (FAZ 2.1 Refactor).

İçerik:
  • send_verification_email : Doğrulama kodu e-postası gönderir (Gmail SMTP SSL)
  • send_report_email       : Analiz PDF raporunu e-posta eki olarak gönderir
"""

import os
import re
import asyncio
import smtplib
import logging
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from app.database.db import get_async_db
from app.services.security import CryptoManager, CryptoDecryptionError

_logger = logging.getLogger("yt_analiz.email")


# ─── Ortak yardımcı: SMTP kimlik bilgilerini DB'den çek ──────────────────────

async def _fetch_smtp_credentials() -> dict:
    db = await get_async_db()
    try:
        async with db.execute(
            "SELECT key, value FROM app_settings WHERE key IN ('smtp_email', 'smtp_password')"
        ) as cursor:
            return {r[0]: r[1] async for r in cursor}
    finally:
        await db.close()


# ─── send_verification_email ─────────────────────────────────────────────────

def send_verification_email(to_email: str, code: str, lang: str = "tr") -> bool:
    """Senkron SMTP gönderimi — SMTP bilgisi parametre olarak alınır veya cache'ten okunur."""
    try:
        rows = asyncio.run(_fetch_smtp_credentials())
        smtp_email = rows.get('smtp_email', '')
        smtp_password = CryptoManager.decrypt(rows.get('smtp_password', ''))

        if not smtp_email or not smtp_password:
            return False

        subjects = {
            "tr": "YouTube Analiz Pro — Doğrulama Kodun",
            "en": "YouTube Analytics Pro — Your Verification Code",
            "es": "YouTube Analytics Pro — Tu Código de Verificación"
        }
        bodies = {
            "tr": f"""Merhaba!

YouTube Analiz Pro hesabını doğrulamak için kodun:

🔑  {code}

Bu kod 15 dakika geçerlidir.
Eğer bu isteği sen yapmadıysan bu maili görmezden gel.

— YouTube Analiz Pro""",
            "en": f"""Hello!

Your verification code for YouTube Analytics Pro:

🔑  {code}

This code is valid for 15 minutes.
If you didn't request this, ignore this email.

— YouTube Analytics Pro""",
            "es": f"""¡Hola!

Tu código de verificación para YouTube Analytics Pro:

🔑  {code}

Este código es válido por 15 minutos.
Si no solicitaste esto, ignora este correo.

— YouTube Analytics Pro"""
        }

        msg = MIMEMultipart()
        msg['From'] = smtp_email
        msg['To'] = to_email
        msg['Subject'] = subjects.get(lang, subjects["tr"])
        msg.attach(MIMEText(bodies.get(lang, bodies["tr"]), 'plain', 'utf-8'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, to_email, msg.as_string())
        return True
    except CryptoDecryptionError:
        raise
    except Exception as e:
        traceback.print_exc()
        print(f"Mail gönderilemedi DETAY: {type(e).__name__}: {e}")
        return False


# ─── send_report_email ───────────────────────────────────────────────────────

def send_report_email(to_email: str, pdf_path: str, video_name: str, lang: str = "tr") -> bool:
    """Analiz raporu PDF'ini kullanıcının e-postasına gönderir."""
    try:
        rows = asyncio.run(_fetch_smtp_credentials())
        smtp_email = rows.get('smtp_email', '')
        smtp_password = CryptoManager.decrypt(rows.get('smtp_password', ''))

        if not smtp_email or not smtp_password:
            return False

        subjects = {
            "tr": f"📊 YouTube Analiz Pro — \"{video_name}\" Raporu",
            "en": f"📊 YouTube Analytics Pro — \"{video_name}\" Report",
            "es": f"📊 YouTube Analytics Pro — Informe de \"{video_name}\""
        }
        bodies = {
            "tr": f"""Merhaba!

"{video_name}" video analizin tamamlandı.
Detaylı APA raporu bu e-postanın ekinde.

Raporundaki önemli noktalar:
• Genel Skor ve Viral Potansiyel
• Thumbnail Duygu ve Kontrast Analizi
• Heyecan Katsayısı (Excitement Score)
• Rakip Kıyaslama ve SEO Check-Up
• AI Koç Tavsiyeleri

Başarılar dileriz!
— YouTube Analiz Pro Ekibi""",
            "en": f"""Hello!

Your video analysis for "{video_name}" is complete.
The detailed APA report is attached to this email.

Key highlights in your report:
• Overall Score and Viral Potential
• Thumbnail Emotion & Contrast Analysis
• Excitement Score Summary
• Competitor Comparison and SEO Check-Up
• AI Coach Recommendations

Best wishes!
— YouTube Analytics Pro Team""",
            "es": f"""¡Hola!

Tu análisis del video "{video_name}" está listo.
El informe APA detallado está adjunto.

Puntos clave del informe:
• Puntuación General y Potencial Viral
• Análisis de Emoción y Contraste de Miniatura
• Resumen de Puntuación de Emoción
• Comparación con Competidores y SEO Check-Up
• Recomendaciones del Coach IA

¡Mucho éxito!
— Equipo YouTube Analytics Pro"""
        }

        msg = MIMEMultipart()
        msg['From'] = smtp_email
        msg['To'] = to_email
        msg['Subject'] = subjects.get(lang, subjects["tr"])
        msg.attach(MIMEText(bodies.get(lang, bodies["tr"]), 'plain', 'utf-8'))

        # PDF ek
        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                part = MIMEBase('application', 'pdf')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                safe_name = re.sub(r'[^\w\-.]', '_', os.path.basename(pdf_path))
                part.add_header('Content-Disposition', f'attachment; filename="{safe_name}"')
                msg.attach(part)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, to_email, msg.as_string())
        _logger.info(f"📧 Rapor e-postası gönderildi: {to_email}")
        return True
    except CryptoDecryptionError:
        raise
    except Exception as e:
        _logger.error(f"Rapor e-postası gönderilemedi: {type(e).__name__}: {e}")
        return False
