#!/usr/bin/env python3
"""
patch_server.py — Predictive Intelligence backend yükseltmesi
Çalıştır: python patch_server.py
"""

import re, shutil, sys
from pathlib import Path

TARGET = Path(__file__).parent / "server.pyw"
BACKUP = TARGET.with_suffix(".pyw.bak_pi")

# ── Dosyayı oku ────────────────────────────────────────────────────────────────
try:
    src = TARGET.read_text(encoding="utf-8")
    enc = "utf-8"
except UnicodeDecodeError:
    try:
        src = TARGET.read_text(encoding="utf-8-sig")
        enc = "utf-8-sig"
    except UnicodeDecodeError:
        src = TARGET.read_text(encoding="cp1254")   # Windows Türkçe fallback
        enc = "cp1254"

print(f"[patch] Dosya okundu: {enc} encoding, {len(src):,} karakter")

# ── Yedek al ──────────────────────────────────────────────────────────────────
shutil.copy2(TARGET, BACKUP)
print(f"[patch] Yedek oluşturuldu: {BACKUP.name}")

changed = 0

# ════════════════════════════════════════════════════════════════════════════════
# DEĞIŞIKLIK 1 — CloneVideoRequest'e Optional alanlar ekle
# ════════════════════════════════════════════════════════════════════════════════

# Optional import kontrolü — eğer yoksa BaseModel importuna ekle
if "from typing import Optional" not in src and "Optional" not in src:
    src = src.replace(
        "from typing import",
        "from typing import Optional,",
    )
    print("[patch] Optional import eklendi")
elif "Optional" not in src:
    # Doğrudan header bölümüne ekle
    src = "from typing import Optional\n" + src
    print("[patch] Optional import başa eklendi")

# CloneVideoRequest'deki son zorunlu alandan sonra Optional alanları ekle.
# Hedef: user_id satırından sonra yeni blok ekle.
OLD_CVR = '    user_id:   int = Field(default=0, description='
NEW_CVR_SUFFIX = '''

    # ── Predictive Intelligence — Opsiyonel Alanlar ───────────────────────────
    # extra="ignore" zaten tanımlı — hiçbirini göndermeden 422 almaz.
    upload_date:       Optional[str]   = Field(default=None, description="ISO 8601 yayın tarihi")
    subscriber_count:  Optional[int]   = Field(default=None, description="Kanal abone sayısı")
    velocity_per_day:  Optional[float] = Field(default=None, description="Günlük tahmini izlenme hızı")
    time_window:       Optional[str]   = Field(default=None, description="fresh/burst/established/evergreen")
    tier:              Optional[str]   = Field(default=None, description="dead/potential/rising/viral/mega_viral")
    penetration_ratio: Optional[float] = Field(default=None, description="İzlenme/Abone oranı")
    comment_signals:   Optional[str]   = Field(default=None, description="İlk 5-10 yorumun ham metni")'''

# Satır bazlı arama (encoding'e karşı dayanıklı)
lines = src.splitlines(keepends=True)
new_lines = []
found_cvr = False
for i, line in enumerate(lines):
    new_lines.append(line)
    if not found_cvr and 'user_id' in line and 'Field(default=0' in line and 'CloneVideoRequest' not in line:
        # Bir sonraki boş satıra veya class bitişine kadar bak
        # Basit yaklaşım: bu satırdan sonra Optional bloğu ekle
        # Sadece CloneVideoRequest içindeyken ekle
        # Geriye bak: son 30 satırda CloneVideoRequest var mı?
        context = ''.join(lines[max(0, i-30):i+1])
        if 'CloneVideoRequest' in context and 'upload_date' not in context:
            new_lines.append(NEW_CVR_SUFFIX + '\n')
            found_cvr = True
            changed += 1
            print("[patch] CloneVideoRequest Optional alanları eklendi")

src = ''.join(new_lines)

# ════════════════════════════════════════════════════════════════════════════════
# DEĞIŞIKLIK 2 — _call_groq_clone() imzasını güncelle + 5 modlu prompt
# ════════════════════════════════════════════════════════════════════════════════

OLD_CLONE_SIG = (
    "async def _call_groq_clone(api_key: str, title: str, channel: str, "
    "transcript: str, content_type: str, purpose: str, views: int = 0) -> str:"
)
NEW_CLONE_SIG = (
    "async def _call_groq_clone(\n"
    "    api_key: str,\n"
    "    title: str,\n"
    "    channel: str,\n"
    "    transcript: str,\n"
    "    content_type: str,\n"
    "    purpose: str,\n"
    "    views: int = 0,\n"
    "    tier: Optional[str] = None,\n"
    "    time_window: Optional[str] = None,\n"
    "    velocity_per_day: Optional[float] = None,\n"
    "    penetration_ratio: Optional[float] = None,\n"
    "    comment_signals: Optional[str] = None,\n"
    ") -> str:"
)

if OLD_CLONE_SIG in src:
    src = src.replace(OLD_CLONE_SIG, NEW_CLONE_SIG, 1)
    changed += 1
    print("[patch] _call_groq_clone imzası güncellendi")
else:
    print("[WARN] _call_groq_clone imzası bulunamadı — satır bazlı deneniyor")
    # Satır bazlı fallback
    src = re.sub(
        r"async def _call_groq_clone\(api_key: str, title: str, channel: str, "
        r"transcript: str, content_type: str, purpose: str, views: int = 0\) -> str:",
        NEW_CLONE_SIG,
        src,
        count=1,
    )
    changed += 1
    print("[patch] _call_groq_clone imzası (regex) güncellendi")

# ── 5 Modlu Prompt bloğunu değiştir ──────────────────────────────────────────
# Mevcut VIRAL_THRESHOLD bloğunu 5 modlu sistem ile değiştir

OLD_THRESHOLD_BLOCK = '''    VIRAL_THRESHOLD = 5_000
    is_viral = views >= VIRAL_THRESHOLD
    thumbnail_rule = _build_thumbnail_rule(content_type)

    # ── Viral: Mevcut prompt'''

NEW_THRESHOLD_BLOCK = '''    thumbnail_rule = _build_thumbnail_rule(content_type)

    # ── Suni Artış Uyarısı ────────────────────────────────────────────────────
    fresh_warning = ""
    if time_window == "fresh":
        fresh_warning = (
            "\\n\\nÖNEMLİ UYARI: Bu video 6 saatten yeni yayınlandı. "
            "İzlenme sayısı ve yorumlar arkadaş ağı etkisi veya suni artış içerebilir. "
            "Analizinde başlık ve thumbnail KALİTESİNE odaklan, izlenme sayısına fazla ağırlık verme."
        )

    # ── Abone Penetrasyon Bağlamı ────────────────────────────────────────────
    penetration_context = ""
    if penetration_ratio is not None:
        if penetration_ratio >= 1.0:
            pen_label = "yüksek"
        elif penetration_ratio >= 0.1:
            pen_label = "orta"
        else:
            pen_label = "düşük"
        penetration_context = (
            f"\\nAbone Penetrasyonu: Bu kanal her 100 abonesine karşılık bu videoda "
            f"{penetration_ratio * 100:.1f} izlenme aldı. Bu {pen_label} bağlılık sinyalidir."
        )

    # ── Yorum Sinyalleri ─────────────────────────────────────────────────────
    comment_context = ""
    if comment_signals and comment_signals.strip():
        comment_context = f"\\nİzleyici Yorumları (ilk 5): {comment_signals[:400]}"

    # ── Velocity Bağlamı ─────────────────────────────────────────────────────
    velocity_context = ""
    if velocity_per_day is not None and velocity_per_day > 0:
        velocity_context = f" ({velocity_per_day:,.0f} izlenme/gün hızında)"

    # ── 5 Kademeli Tier Tespiti ───────────────────────────────────────────────
    # Frontend'den tier gelmezse izlenmeye göre hesapla
    effective_tier = tier or (
        "mega_viral" if views >= 100_000 else
        "viral"      if views >= 5_000   else
        "potential"  if views >= 500     else
        "dead"
    )

    # Tier'a göre AI tonu ve anatomi direktifi
    if effective_tier == "dead":
        views_info       = f"yalnızca {views:,} izlenme{velocity_context}" if views > 0 else "sıfıra yakın izlenme"
        ai_tone          = "Acil müdahale uzmanı gibi konuş. Sorunun kaynağını teşhis et."
        anatomi_label    = "VİDEO OTOPSİ (Neden Hiç Kitle Bulamadı?)"
        anatomi_content  = (
            "Bu videonun neden kitle bulamadığını (zayıf başlık, thumbnail sorunu, "
            "kanca eksikliği, yayın zamanı vb.) 2-3 cümleyle analiz et. "
            "Somut, uygulanabilir müdahale önerileri sun."
        )

    elif effective_tier == "potential":
        views_info       = f"{views:,} izlenme{velocity_context}" if views > 0 else "düşük izlenme"
        ai_tone          = "Koç gibi konuş — potansiyel var ama bir şeyler eksik."
        anatomi_label    = "POTANSİYEL ANALİZİ (Bir Hamle Eksik)"
        anatomi_content  = (
            "Bu videonun neden daha fazla izlenme alamadığını ve hangi küçük değişiklikle "
            "(başlık testi, thumbnail A/B, farklı dağıtım kanalı) kitleye ulaşabileceğini açıkla."
        )

    elif effective_tier == "rising":
        views_info       = f"{views:,} izlenme{velocity_context}" if views > 0 else "yükselen izlenme"
        ai_tone          = "Heyecanlı ve acil konuş — bu video ŞU AN patlıyor olabilir!"
        anatomi_label    = "MOMENTUM ANALİZİ (Bu Video Neden Yükseliyor?)"
        anatomi_content  = (
            "Bu videonun şu an momentum kazanmasının nedenini analiz et. "
            "Patlama penceresini yakalarken uygulanabilecek ivme stratejileri sun."
        )

    elif effective_tier == "viral":
        views_info       = f"{views:,} izlenme{velocity_context}" if views > 0 else "yüksek izlenme"
        ai_tone          = "Analist gibi konuş — başarının anatomisini çıkart."
        anatomi_label    = "VİRAL ANATOMİ (Bu Video Neden Patladı?)"
        anatomi_content  = (
            "Bu videonun viral olmasındaki psikolojik tetikleyiciyi ve kanca mekanizmasını "
            "2-3 cümleyle analiz et. Tekrarlanabilir kalıpları vurgula."
        )

    else:  # mega_viral
        views_info       = f"{views:,} izlenme{velocity_context}" if views > 0 else "mega viral izlenme"
        ai_tone          = "Sistemi çıkart — kazayı kopyalama, tekrarlanabilir unsurları ayır."
        anatomi_label    = "MEGA VİRAL ANATOMİ (Algoritma Kırıcı Formül)"
        anatomi_content  = (
            "Bu mega viral videonun altındaki sistemi ve algoritma dinamiğini ortaya çıkar. "
            "Taklit edilebilir unsurları (format, kanca tipi, thumbnail psikolojisi) ayır. "
            "Sadece bu videoyu değil, bu videonun yarattığı kalıbı klonla."
        )

    anatomi_directive = f"""1. {anatomi_label}: {anatomi_content}"""
    # Mevcut prompt'''

if OLD_THRESHOLD_BLOCK in src:
    src = src.replace(OLD_THRESHOLD_BLOCK, NEW_THRESHOLD_BLOCK, 1)
    changed += 1
    print("[patch] _call_groq_clone 5-modlu tier bloğu eklendi")
else:
    # Regex fallback
    pattern = r"    VIRAL_THRESHOLD = 5_000\s+is_viral = views >= VIRAL_THRESHOLD\s+thumbnail_rule = _build_thumbnail_rule\(content_type\)"
    if re.search(pattern, src):
        src = re.sub(pattern, NEW_THRESHOLD_BLOCK.rstrip(), src, count=1)
        changed += 1
        print("[patch] _call_groq_clone tier bloğu (regex) güncellendi")
    else:
        print("[WARN] _call_groq_clone tier bloğu bulunamadı")

# ── Prompt içindeki eski is_viral referanslarını yeni tier'e uyarla ──────────
# views_info tanımları artık yukarıda — prompt içindeki eski if is_viral bloğunu kaldır
OLD_VIRAL_IF = """    if is_viral:
        views_info = f\"{views:,} izlenme\" if views > 0 else \"Yüksek izlenme\"
        anatomi_directive = f\"\"\"1. VİRAL ANATOMİ: Bu video {views_info} almış. Neden viral olduğunu (psikolojik tetikleyici ve kanca) analiz et.\"\"\"
    # ── Viral Değil: Potansiyel analizi promptu ──────────────────────────────────────────────────────────────
    else:
        views_info = f\"yaln\\u0131zca {views:,} izlenme\" if views > 0 else \"\\u00e7ok d\\u00fc\\u015f\\u00fck izlenme\"
        anatomi_directive = f\"\"\"1. VİDEO ANALİZİ (ÖNEMLİ): Bu video henüz {views_info} almış ve viral DEĞİLDİR. \n\\\"Viral Anatomi\\\" başlığını KULLANMA. Bunun yerine \"viral_anatomi\" alanında şu bilgileri yaz:\n- Bu videonun neden kitle bulamadığını (zayıf başlık, thumbnail sorunu, kanca eksikliği vb.) 2-3 cümleyle analiz et.\n- Videonun çıkarmaya çalıştığı potansiyeli ve ne yaparsa kitleye ulaşabileceğini açıklayıcı öneriler sun.\"\"\""""

if OLD_VIRAL_IF in src:
    src = src.replace(OLD_VIRAL_IF, "", 1)
    changed += 1
    print("[patch] Eski is_viral if bloğu temizlendi")

# ── Prompt f-string içindeki eski is_viral referansını yeni ile değiştir ─────
# "{'Neden patlad..." gibi inline conditional'ı kaldır
OLD_INLINE_COND = "\"{'Neden patlad\\u0131\\u011f\\u0131n\\u0131 anlatan 2-3 c\\u00fcmlelik psikolojik analiz' if is_viral else 'Neden kitle bulamad\\u0131\\u011f\\u0131n\\u0131 ve potansiyelini a\\u015fa \\u00e7\\u0131karmak i\\u00e7in ne yap\\u0131lmas\\u0131 gerekti\\u011fini anlatan 2-3 c\\u00fcmle'}\""
if OLD_INLINE_COND in src:
    src = src.replace(OLD_INLINE_COND, '"Tier bazlı AI direktifi yukarıda tanımlandı"', 1)
    changed += 1
    print("[patch] Inline is_viral conditional kaldırıldı")

# ── Prompt şablonunu geliştir: extra context ekle ────────────────────────────
OLD_VIEWS_LINE = '📊 İzlenme Durumu: {views_info}'
NEW_VIEWS_BLOCK = """📊 İzlenme Durumu: {views_info}{fresh_warning}{penetration_context}{comment_context}"""

if OLD_VIEWS_LINE in src:
    src = src.replace(OLD_VIEWS_LINE, NEW_VIEWS_BLOCK, 1)
    changed += 1
    print("[patch] Prompt'a fresh_warning + penetration_context + comment_context eklendi")
else:
    # Türkçe karakter encoding farklılığı için regex
    pattern = r'📊 [İI]zlenme Durumu: \{views_info\}'
    if re.search(pattern, src):
        src = re.sub(pattern, NEW_VIEWS_BLOCK, src, count=1)
        changed += 1
        print("[patch] Prompt views satırı (regex) güncellendi")

# ── Ton direktifini promptun başına ekle ─────────────────────────────────────
OLD_PROMPT_START = 'prompt = f"""Sen üst düzey bir YouTube Algoritma Uzmanı ve İçerik Stratejistisin.'
NEW_PROMPT_START = 'prompt = f"""Sen üst düzey bir YouTube Algoritma Uzmanı ve İçerik Stratejistisin. {ai_tone}'

if OLD_PROMPT_START in src:
    src = src.replace(OLD_PROMPT_START, NEW_PROMPT_START, 1)
    changed += 1
    print("[patch] Prompt AI tonu direktifi eklendi")

# ════════════════════════════════════════════════════════════════════════════════
# DEĞIŞIKLIK 3 — _call_groq_clone çağrı sitesini güncelle
# ════════════════════════════════════════════════════════════════════════════════

OLD_CLONE_CALL = (
    "        result = await _call_groq_clone("
    "api_key, title, channel, transcript, content_type, purpose, views=payload.views)"
)
NEW_CLONE_CALL = (
    "        result = await _call_groq_clone(\n"
    "            api_key, title, channel, transcript, content_type, purpose,\n"
    "            views=payload.views,\n"
    "            tier=payload.tier,\n"
    "            time_window=payload.time_window,\n"
    "            velocity_per_day=payload.velocity_per_day,\n"
    "            penetration_ratio=payload.penetration_ratio,\n"
    "            comment_signals=payload.comment_signals,\n"
    "        )"
)

if OLD_CLONE_CALL in src:
    src = src.replace(OLD_CLONE_CALL, NEW_CLONE_CALL, 1)
    changed += 1
    print("[patch] _call_groq_clone çağrı sitesi güncellendi")
else:
    print("[WARN] _call_groq_clone çağrı sitesi bulunamadı")

# ════════════════════════════════════════════════════════════════════════════════
# DEĞIŞIKLIK 4 — _call_groq_debate imzasını güncelle
# ════════════════════════════════════════════════════════════════════════════════

OLD_DEBATE_SIG = "    views: int = 0,\n) -> dict:"
NEW_DEBATE_SIG = (
    "    views: int = 0,\n"
    "    tier: Optional[str] = None,\n"
    "    time_window: Optional[str] = None,\n"
    "    velocity_per_day: Optional[float] = None,\n"
    "    penetration_ratio: Optional[float] = None,\n"
    "    comment_signals: Optional[str] = None,\n"
    ") -> dict:"
)

# _call_groq_debate context içinde bul (birden fazla olabilir, doğrusunu seç)
debate_func_pos = src.find("async def _call_groq_debate(")
if debate_func_pos != -1:
    # Fonksiyon imzası bölgesinde güncelle
    sig_search_area = src[debate_func_pos: debate_func_pos + 600]
    if "    views: int = 0,\n) -> dict:" in sig_search_area:
        # Bu kısımdaki ilk oluşumu değiştir
        before = src[:debate_func_pos]
        after_start = src[debate_func_pos:]
        after_start = after_start.replace(OLD_DEBATE_SIG, NEW_DEBATE_SIG, 1)
        src = before + after_start
        changed += 1
        print("[patch] _call_groq_debate imzası güncellendi")
    else:
        print("[WARN] _call_groq_debate imzasında views satırı farklı")
else:
    print("[WARN] _call_groq_debate fonksiyonu bulunamadı")

# ════════════════════════════════════════════════════════════════════════════════
# DEĞIŞIKLIK 5 — _call_groq_debate 5-modlu anatomi direktifi
# ════════════════════════════════════════════════════════════════════════════════

OLD_DEBATE_VIRAL = """    VIRAL_THRESHOLD = 5_000
    is_viral = views >= VIRAL_THRESHOLD

    if is_viral:
        views_info = f\"{views:,} izlenme\" if views > 0 else \"Yüksek izlenme\"
        anatomi_directive = (
            \"KURAL 1 (ZORUNLU BAŞLANGIÇ):\\\\n\"
            f\"Bu videonun {views_info} aldığını unutma. \"
            \"Başarısının altındaki psikolojik tetikleyiciyi \\\\\"viral_anatomi\\\\\" alanında açıkla.\"
        )
    else:
        views_info = f\"yaln\\u0131zca {views:,} izlenme\" if views > 0 else \"\\u00e7ok d\\u00fc\\u015f\\u00fck izlenme\"
        anatomi_directive = (
            \"KURAL 1 (ZORUNLU BAŞLANGIÇ — ÖNEMLİ):\\\\n\"
            f\"Bu video henüz {views_info} almış ve viral DEĞİLDİR. \"
            \"\\\\\"viral_anatomi\\\\\" alanını YALNIZCA şu bilgilerle doldurun: \"
            \"Bu videonun neden kitle bulamadığını (başlık zayıflığı, thumbnail, kanca eksikliği vb.) ve \"
            \"ne yaparsa viral olabileceğini 2-3 cümleyle açıkla. 'Neden patladı' benzeri ifadeler KULLANMA.\"
        )"""

NEW_DEBATE_VIRAL = """    # ── Suni Artış Uyarısı (Hakem için) ────────────────────────────────────
    debate_fresh_warning = ""
    if time_window == "fresh":
        debate_fresh_warning = (
            "\\nÖNEMLİ: Bu video 6 saatten yeni. İzlenme henüz stabil değil — "
            "başlık ve thumbnail kalitesine odaklan."
        )

    # ── Penetrasyon Bağlamı (Hakem için) ─────────────────────────────────────
    debate_pen_ctx = ""
    if penetration_ratio is not None:
        pen_lbl = "yüksek" if penetration_ratio >= 1.0 else ("orta" if penetration_ratio >= 0.1 else "düşük")
        debate_pen_ctx = (
            f"\\nAbone Penetrasyon: Her 100 aboneye {penetration_ratio * 100:.1f} izlenme "
            f"→ {pen_lbl} bağlılık."
        )

    # ── Yorum sinyali (hakem için) ────────────────────────────────────────────
    debate_comment_ctx = ""
    if comment_signals and comment_signals.strip():
        debate_comment_ctx = f"\\nİzleyici Yorumları: {comment_signals[:300]}"

    # ── Velocity (hakem için) ────────────────────────────────────────────────
    debate_vel_ctx = ""
    if velocity_per_day is not None and velocity_per_day > 0:
        debate_vel_ctx = f" ({velocity_per_day:,.0f} izlenme/gün)"

    # ── 5 Kademeli Tier ──────────────────────────────────────────────────────
    effective_tier_d = tier or (
        "mega_viral" if views >= 100_000 else
        "viral"      if views >= 5_000   else
        "potential"  if views >= 500     else
        "dead"
    )

    if effective_tier_d == "dead":
        views_info = f"yalnızca {views:,} izlenme{debate_vel_ctx}" if views > 0 else "sıfıra yakın izlenme"
        anatomi_directive = (
            "KURAL 1 (ACİL MÜDAHALE):\\n"
            f"Bu video {views_info} aldı ve viral değil. "
            "\\\"viral_anatomi\\\" alanında bu videonun başlık/thumbnail/kanca sorunlarını teşhis et."
        )
    elif effective_tier_d == "potential":
        views_info = f"{views:,} izlenme{debate_vel_ctx}" if views > 0 else "düşük izlenme"
        anatomi_directive = (
            "KURAL 1 (POTANSİYEL KOÇLUĞU):\\n"
            f"Bu video {views_info} ile potansiyel sınırında. "
            "\\\"viral_anatomi\\\" alanında eksik hamleyi ve kanca/dağıtım tamir önerilerini yaz."
        )
    elif effective_tier_d == "rising":
        views_info = f"{views:,} izlenme{debate_vel_ctx}" if views > 0 else "yükselen izlenme"
        anatomi_directive = (
            "KURAL 1 (MOMENTUM YAKALAMA — ACİL!):\\n"
            f"Bu video {views_info} ile ŞU AN yükseliyor! "
            "\\\"viral_anatomi\\\" alanında momentum kazanma sebebini ve ivme stratejisini açıkla."
        )
    elif effective_tier_d == "viral":
        views_info = f"{views:,} izlenme{debate_vel_ctx}" if views > 0 else "yüksek izlenme"
        anatomi_directive = (
            "KURAL 1 (BAŞARI ANATOMİSİ):\\n"
            f"Bu videonun {views_info} aldığını unutma. "
            "\\\"viral_anatomi\\\" alanında başarısının psikolojik tetikleyicisini ve tekrarlanabilir kalıbını çıkart."
        )
    else:  # mega_viral
        views_info = f"{views:,} izlenme{debate_vel_ctx}" if views > 0 else "mega viral izlenme"
        anatomi_directive = (
            "KURAL 1 (MEGA VİRAL — SİSTEMİ ÇIKART):\\n"
            f"Bu video {views_info} ile mega viral. "
            "\\\"viral_anatomi\\\" alanında algoritma kırıcı formülü ve tekrarlanabilir unsurları ayır."
        )"""

if OLD_DEBATE_VIRAL in src:
    src = src.replace(OLD_DEBATE_VIRAL, NEW_DEBATE_VIRAL, 1)
    changed += 1
    print("[patch] _call_groq_debate 5-modlu tier bloğu eklendi")
else:
    # Basit is_viral bloğu arama (regex)
    pattern = r"    VIRAL_THRESHOLD = 5_000\s+is_viral = views >= VIRAL_THRESHOLD\s+\s+if is_viral:"
    m = re.search(pattern, src)
    if m:
        # debate fonksiyonu içinde mi?
        debate_pos = src.find("async def _call_groq_debate(")
        if debate_pos != -1 and m.start() > debate_pos:
            # Blok sonunu bul (else bloğunun bitişi)
            block_end = src.find('\n\n    prompt_judge', m.start())
            if block_end == -1:
                block_end = src.find('\n\n    transcript_excerpt', m.start())
            if block_end != -1:
                src = src[:m.start()] + NEW_DEBATE_VIRAL + src[block_end:]
                changed += 1
                print("[patch] _call_groq_debate tier bloğu (regex) güncellendi")
            else:
                print("[WARN] _call_groq_debate tier bloğunun sonu bulunamadı")
    else:
        print("[WARN] _call_groq_debate eski tier bloğu bulunamadı")

# ── Debate hakem promptuna extra context ekle ─────────────────────────────────
OLD_DEBATE_VIEWS_LINE = '📊 İzlenme Durumu: {views_info}'
NEW_DEBATE_VIEWS_BLOCK = "📊 İzlenme Durumu: {views_info}{debate_fresh_warning}{debate_pen_ctx}{debate_comment_ctx}"

# Sadece debate fonksiyonu içindeki views satırını değiştir (clone prompt'ından sonra geleni)
debate_start = src.find("async def _call_groq_debate(")
if debate_start != -1:
    before_debate = src[:debate_start]
    after_debate = src[debate_start:]
    if OLD_DEBATE_VIEWS_LINE in after_debate:
        after_debate = after_debate.replace(OLD_DEBATE_VIEWS_LINE, NEW_DEBATE_VIEWS_BLOCK, 1)
        src = before_debate + after_debate
        changed += 1
        print("[patch] Debate hakem promptuna extra context eklendi")
    else:
        print("[WARN] Debate hakem promptunda views_info satırı bulunamadı")

# ════════════════════════════════════════════════════════════════════════════════
# DEĞIŞIKLIK 6 — _call_groq_debate çağrı sitesini güncelle
# ════════════════════════════════════════════════════════════════════════════════

OLD_DEBATE_CALL = (
    "    debate_result = await _call_groq_debate("
    "api_key, title, channel, transcript, content_type, purpose, views=payload.views)"
)
NEW_DEBATE_CALL = (
    "    debate_result = await _call_groq_debate(\n"
    "        api_key, title, channel, transcript, content_type, purpose,\n"
    "        views=payload.views,\n"
    "        tier=payload.tier,\n"
    "        time_window=payload.time_window,\n"
    "        velocity_per_day=payload.velocity_per_day,\n"
    "        penetration_ratio=payload.penetration_ratio,\n"
    "        comment_signals=payload.comment_signals,\n"
    "    )"
)

if OLD_DEBATE_CALL in src:
    src = src.replace(OLD_DEBATE_CALL, NEW_DEBATE_CALL, 1)
    changed += 1
    print("[patch] _call_groq_debate çağrı sitesi güncellendi")
else:
    print("[WARN] _call_groq_debate çağrı sitesi bulunamadı")

# ════════════════════════════════════════════════════════════════════════════════
# Kaydet
# ════════════════════════════════════════════════════════════════════════════════

TARGET.write_text(src, encoding=enc)
print(f"\n[patch] ✅ Tamamlandı — {changed} değişiklik uygulandı")
print(f"[patch] Dosya kaydedildi: {TARGET.name} ({enc})")

if changed == 0:
    print("[patch] UYARI: Hiçbir değişiklik yapılamadı — pattern'lar dosyada bulunamadı.")
    sys.exit(1)
