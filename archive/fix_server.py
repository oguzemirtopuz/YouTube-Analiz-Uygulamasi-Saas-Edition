"""
Surgical fix for server.pyw:
1. Restore line 2964 to its original content (remove injected new-code fragment).
2. Replace the OLD _call_groq_clone body (lines ~3044-3122) with the corrected version.
"""

import re

filepath = r"d:\Projeler - Kopya\analizprofinal-main\analizprofinal-main\server.pyw"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# ── FIX 1: Restore corrupt line 2964 ──────────────────── ─────────────────────
# The line looks like:
# " # YouTube usually has subtitles in JSON3 format? # ── Viral: Current prompt ──"
# We need to restore just the original part.
CORRUPT_LINE = (
    "            # YouTube genellikle JSON3 formatında subtitle d"
    # Whatever garbage is after the '?' up to the injected code
)
# Use a regex to find the corrupted line and restore it
content = re.sub(
    r"(            # YouTube genellikle JSON3 format[^\n]*?)    # [^\n]* Viral: Mevcut prompt [^\n]*",
    r"            # YouTube genellikle JSON3 formatında subtitle döner",
    content
)

# ── FIX 2: Remove the injected block that was placed before _build_thumbnail_rule ends ─
# The injected block starts right after line 2963 and contains the new if/else/prompt code
# that was supposed to go inside _call_groq_clone. We need to remove it.
# It starts with "\n if is_viral:\n # views=0 here theoretical" and ends before
# "async def _call_groq_clone"

INJECTED_START = "\n    if is_viral:\n        # views=0 burada teorik olarak imkânsız"
INJECTED_END = "\nasync def _call_groq_clone("

idx_start = content.find(INJECTED_START)
idx_end = content.find(INJECTED_END, idx_start)

if idx_start != -1 and idx_end != -1:
    # Remove the injected block
    content = content[:idx_start] + "\n" + content[idx_end:]
    print(f"✅ FIX 2: Removed injected block ({idx_end - idx_start} chars)")
else:
    print(f"⚠️  FIX 2: Could not find injected block. idx_start={idx_start}, idx_end={idx_end}")

# ── FIX 3: Replace the OLD _call_groq_clone body with the corrected version ──
OLD_CLONE_BODY = '''async def _call_groq_clone(api_key: str, title: str, channel: str, transcript: str, content_type: str, purpose: str, views: int = 0) -> str:
    """
    Groq Llama-3 ile viral klonlama / potansiyel analizi konsepti üretir.
    views >= 5000 ise viral analiz modu, views < 5000 ise "viral değil" potansiyel analizi modu kullanılır.
    Senkron requests çağrısını run_in_threadpool ile sarmalar.
    """
    VIRAL_THRESHOLD = 5_000
    is_viral = views >= VIRAL_THRESHOLD
    thumbnail_rule = _build_thumbnail_rule(content_type)

    # ── Viral: Current prompt ────────────────────────── ───────────────────────────
    if is_viral:
        views_info = f"{views:,} izlenme" if views > 0 else "Yüksek izlenme"
        anatomi_directive = f"""1. VİRAL ANATOMİ: Bu video {views_info} almış. Neden viral olduğunu (psikolojik tetikleyici ve kanca) analiz et."""
    # ── Not Viral: Potential analysis prompt ───────────────────────────────
    else:
        views_info = f"yalnızca {views:,} izlenme" if views > 0 else "çok düşük izlenme"
        anatomi_directive = f"""1. VİDEO ANALİZİ (ÖNEMLİ): Bu video henüz {views_info} almış ve viral DEĞİLDİR. \n"Viral Anatomi" başlığını KULLANMA. Bunun yerine "viral_anatomi" alanında şu bilgileri yaz:\n- Bu videonun neden kitle bulamadığını (zayıf başlık, thumbnail sorunu, kanca eksikliği vb.) 2-3 cümleyle analiz et.\n- Videonun çıkarmaya çalıştığı potansiyeli ve ne yaparsa kitleye ulaşabileceğini açıklayıcı öneriler sun."""

    prompt = f"""Sen üst düzey bir YouTube Algoritma Uzmanı ve İçerik Stratejistisin. 

KULLANICI PROFİLİ: 
Bu analizi isteyen kullanıcının kanalı 'BabaClutch'. Konsepti: Oyun (Minecraft, Rocket League vb.), Kaos, Rage, Arkadaş Kavgası ve Yüksek Enerji.

GÖREVİN: 
Sana verilen orijinal video başlığı ve altyazı (transcript) verilerini analiz ederek, bu videonun ruhunu klonlayacak 3 yeni, özgün ve yüksek potansiyelli video fikri üretmek.

📌 Orijinal Başlık: {title}
📺 Orijinal Kanal: {channel}
📊 İzlenme Durumu: {views_info}
📝 Senaryo (ilk 2000 karakter):
{transcript[:2000] if transcript else "[UYARI: Altyazı bulunamadı. Yalnızca video başlığına dayanarak analiz yap. Kesinlikle içerik uydurmaya çalışma.]"}

KURALLAR:
{anatomi_directive}
2. FİKİR ÜRETİMİ: Orijinal videonun ruhunu kopyalayan 3 farklı video fikri sun.
{thumbnail_rule}
3. NİŞ UYARISI: Analiz ettiğin video, kullanıcının "Oyun/Kaos" konseptiyle uyuşmuyorsa bir uyarı metni yaz. Uyuşuyorsa boş bırak.
4. KESİN FORMAT KURALI: Çıktın KESİNLİKLE bir dizi (array) [...] OLAMAZ. Çıktın KESİNLİKLE bir obje (object) {{...}} olmak zorundadır. Objenin içinde "viral_anatomi", "nis_uyarisi" ve "fikirler" anahtarları ZORUNLUDUR. SADECE AŞAĞIDAKİ JSON FORMATINDA ÇIKTI VER (Başka hiçbir düz metin yazma):
{{
  "viral_anatomi": "{'Neden patladığını anlatan 2-3 cümlelik psikolojik analiz' if is_viral else 'Neden kitle bulamadığını ve potansiyelini açığa çıkarmak için ne yapılması gerektiğini anlatan 2-3 cümle'}",
  "nis_uyarisi": "Oyun/kaos dışındaysa uyarı metni, yoksa boş string",
  "fikirler": [
    {{
       "title": "...",
       "hook": "...",
       "thumbnail": "..."
    }}
  ]
}}"""'''

NEW_CLONE_BODY = '''async def _call_groq_clone(api_key: str, title: str, channel: str, transcript: str, content_type: str, purpose: str, views: int = 0) -> str:
    """
    Groq Llama-3 ile viral klonlama / potansiyel analizi konsepti üretir.
    views >= 5000 ise viral analiz modu, views < 5000 ise "viral değil" potansiyel analizi modu kullanılır.
    Senkron requests çağrısını run_in_threadpool ile sarmalar.
    """
    VIRAL_THRESHOLD = 5_000
    is_viral = views >= VIRAL_THRESHOLD
    thumbnail_rule = _build_thumbnail_rule(content_type)

    # ── Viral: Current prompt ────────────────────────── ───────────────────────────
    if is_viral:
        # views=0 is theoretically impossible here (is_viral=True requires views>=5000)
        views_info = f"{views:,} izlenme"
        anatomi_directive = "1. VİRAL ANATOMİ: Bu video neden viral oldu? İzleyiciyi çeken psikolojik tetikleyiciyi ve kancayı analiz et."
    # ── Not Viral: Potential analysis prompt ───────────────────────────────
    else:
        # views=0 → YouTube may not have uploaded viewing data to the page (new video, hidden counter, etc.)
        # Instead of reflecting this situation to the AI ​​as "too low", we clearly explain it as "data could not be received".
        if views > 0:
            views_info = f"yalnızca {views:,} izlenme"
            views_context = f"Bu video şu an yalnızca {views:,} izlenmeye sahip ve viral DEĞİLDİR."
        else:
            views_info = "İzlenme verisi alınamadı (yeni video veya gizli sayaç)"
            views_context = "Bu videonun izlenme sayısı tespit edilemedi (yeni yüklenmiş veya YouTube sayacı henüz görünmüyor). Viral olmadığını varsay."
        anatomi_directive = f"""1. VİDEO ANALİZİ (ÖNEMLİ): {views_context}
"Viral Anatomi" veya "Neden Patladı" gibi başlıklar KULLANMA.
"viral_anatomi" alanında şunları yaz:
- Bu videonun başlık, thumbnail veya kanca açısından neden kitleye ulaşamadığını 2-3 cümleyle analiz et.
- Videonun potansiyelini ortaya çıkarmak için somut öneriler sun.
- Altyazı yoksa yalnızca başlık verisine dayanarak dürüst bir değerlendirme yap, UYDURMA."""

    # Explicitly warn AI if there are no subtitles (hallucination shield)
    transcript_section = (
        transcript[:2000]
        if transcript
        else "[UYARI: Altyazı bulunamadı. Yalnızca video başlığına dayanarak analiz yap. Kesinlikle içerik uydurmaya çalışma.]"
    )

    # viral_anatomy description in JSON example — plain text, not Python expression
    anatomi_example = (
        "Neden patladığını anlatan 2-3 cümlelik psikolojik analiz"
        if is_viral
        else "Neden kitle bulamadığını ve potansiyelini açığa çıkarmak için ne yapılması gerektiğini anlatan 2-3 cümle"
    )

    prompt = f"""Sen üst düzey bir YouTube Algoritma Uzmanı ve İçerik Stratejistisin. 

KULLANICI PROFİLİ: 
Bu analizi isteyen kullanıcının kanalı 'BabaClutch'. Konsepti: Oyun (Minecraft, Rocket League vb.), Kaos, Rage, Arkadaş Kavgası ve Yüksek Enerji.

GÖREVİN: 
Sana verilen orijinal video başlığı ve altyazı (transcript) verilerini analiz ederek, bu videonun ruhunu klonlayacak 3 yeni, özgün ve yüksek potansiyelli video fikri üretmek.

📌 Orijinal Başlık: {title}
📺 Orijinal Kanal: {channel}
📊 İzlenme Durumu: {views_info}
📝 Senaryo (ilk 2000 karakter):
{transcript_section}

KURALLAR:
{anatomi_directive}
2. FİKİR ÜRETİMİ: Orijinal videonun ruhunu kopyalayan 3 farklı video fikri sun.
{thumbnail_rule}
3. NİŞ UYARISI: Analiz ettiğin video, kullanıcının "Oyun/Kaos" konseptiyle uyuşmuyorsa bir uyarı metni yaz. Uyuşuyorsa boş bırak.
4. KESİN FORMAT KURALI: Çıktın KESİNLİKLE bir dizi (array) [...] OLAMAZ. Çıktın KESİNLİKLE bir obje (object) {{...}} olmak zorundadır. Objenin içinde "viral_anatomi", "nis_uyarisi" ve "fikirler" anahtarları ZORUNLUDUR. SADECE AŞAĞIDAKİ JSON FORMATINDA ÇIKTI VER (Başka hiçbir düz metin yazma):
{{
  "viral_anatomi": "{anatomi_example}",
  "nis_uyarisi": "Oyun/kaos dışındaysa uyarı metni, yoksa boş string",
  "fikirler": [
    {{
       "title": "...",
       "hook": "...",
       "thumbnail": "..."
    }}
  ]
}}"""'''

if OLD_CLONE_BODY in content:
    content = content.replace(OLD_CLONE_BODY, NEW_CLONE_BODY, 1)
    print("✅ FIX 3: Replaced old _call_groq_clone body with corrected version")
else:
    print("⚠️  FIX 3: Could not find exact old body. Trying partial match...")
    # Fallback: find via signature
    sig = 'async def _call_groq_clone(api_key: str, title: str, channel: str, transcript: str, content_type: str, purpose: str, views: int = 0) -> str:'
    idx = content.find(sig)
    if idx != -1:
        print(f"  Found signature at char {idx}")
        # Find next function definition after this
        next_fn = re.search(r'\ndef calculate_chaos_score', content[idx:])
        if next_fn:
            old_body = content[idx:idx+next_fn.start()]
            print(f"  Old body length: {len(old_body)} chars")
            content = content[:idx] + NEW_CLONE_BODY + content[idx+next_fn.start():]
            print("✅ FIX 3 (fallback): Replaced via signature match")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("\n✅ All fixes written. Verifying...")

# verification
with open(filepath, "r", encoding="utf-8") as f:
    verify = f.read()

check1 = "views_context" in verify
check2 = verify.count("async def _call_groq_clone") == 1
check3 = "transcript_section" in verify
check4 = "anatomi_example" in verify
# Old Python expression should be gone from clone prompt
check5 = "{'Neden patladığını anlatan" not in verify

print(f"  views_context present: {check1}")
print(f"  Single _call_groq_clone definition: {check2}")
print(f"  transcript_section present: {check3}")
print(f"  anatomi_example present: {check4}")
print(f"  Old Python f-string expression removed: {check5}")

if all([check1, check2, check3, check4, check5]):
    print("\n🟢 ALL CHECKS PASSED — server.pyw is clean")
else:
    print("\n🔴 SOME CHECKS FAILED — manual review needed")
