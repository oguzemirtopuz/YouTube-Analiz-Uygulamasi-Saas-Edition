import re

TURKISH = re.compile(r'[\u015f\u011f\u00fc\u00f6\u00e7\u0131\u0130\u015e\u011e\u00dc\u00d6\u00c7\u015F\u011F\u00FC\u00D6\u00C7\u0131\u0130]')

with open('server.pyw', encoding='utf-8') as f:
    lines = f.readlines()

remaining = []
for i, line in enumerate(lines, 1):
    if TURKISH.search(line):
        remaining.append((i, line.rstrip()))

print(f'Lines with Turkish characters remaining: {len(remaining)}')
for ln, text in remaining[:50]:
    print(f'  Line {ln}: {text[:130]}')
