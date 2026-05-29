"""
categorized_turkish_scan.py
Scans server.pyw and groups remaining Turkish-character lines into:
  A) AI prompt content (intentional multilingual: tr/en/es branches)
  B) NLP keyword lists (Turkish-language detection data)
  C) Genuinely untranslated — should be fixed
"""
import re
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TURKISH_RE = re.compile(r'[\u015f\u011f\u00fc\u00f6\u00e7\u0131\u0130\u015e\u011e\u00dc\u00d6\u00c7]')

# Known-intentional line ranges (AI prompts in tr/en/es, NLP keyword lists)
INTENTIONAL_RANGES = [
    (1090, 1110),   # trilingual AI prompt template (tr branch)
    (1280, 1285),   # ret_keywords NLP list
    (1310, 1315),   # hook_words NLP Turkish list
    (1800, 1815),   # broad_keywords language-detection list
    (1910, 1925),   # content category NLP keywords
    (1985, 1995),   # Turkish title fallback (intentional locale)
    # AI prompts sent to Groq (Turkish-language instruction variants)
    (2695, 2720),
    (3040, 3110),
    (3330, 3380),
    (3590, 3610),
    (3875, 3910),
    (3988, 4040),
]

def is_intentional(lineno):
    for start, end in INTENTIONAL_RANGES:
        if start <= lineno <= end:
            return True
    return False

with open('server.pyw', encoding='utf-8') as f:
    lines = f.readlines()

categories = {'intentional': [], 'needs_fix': []}

for i, line in enumerate(lines, 1):
    if TURKISH_RE.search(line):
        if is_intentional(i):
            categories['intentional'].append((i, line.rstrip()))
        else:
            categories['needs_fix'].append((i, line.rstrip()))

print(f"=== INTENTIONAL (AI prompts / NLP data): {len(categories['intentional'])} lines ===")
for ln, text in categories['intentional'][:5]:
    print(f"  L{ln}: {text[:100]}")
if len(categories['intentional']) > 5:
    print(f"  ... and {len(categories['intentional'])-5} more (all expected)")

print(f"\n=== NEEDS FIX: {len(categories['needs_fix'])} lines ===")
for ln, text in categories['needs_fix']:
    print(f"  L{ln}: {text[:120]}")

print("\nDone.")
