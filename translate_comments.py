# -*- coding: utf-8 -*-
import os
import re
from deep_translator import GoogleTranslator

translator = GoogleTranslator(source='tr', target='en')

def translate_text(text):
    if not re.search(r'[a-zA-Z]', text):
        return text
    try:
        translated = translator.translate(text)
        return translated if translated else text
    except Exception as e:
        return text

def translate_file(filepath):
    print("Processing", filepath)
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()

    lines = source.split('\n')
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith('#'):
            indent = line[:len(line) - len(stripped)]
            comment_text = stripped[1:].strip()
            if comment_text:
                translated = translate_text(comment_text)
                lines[i] = f"{indent}# {translated}"
        elif '#' in line:
            parts = line.split('#', 1)
            if '"' not in parts[0] and "'" not in parts[0]:
                translated = translate_text(parts[1].strip())
                lines[i] = f"{parts[0]}# {translated}"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

files = [
    'server.pyw', 'fix_server.py', 'patch_server.py', 'update.py',
    'app/database/db.py', 'app/services/ai_service.py', 
    'app/services/analysis_engine.py', 'app/services/competitor.py',
    'app/services/email_service.py', 'app/services/security.py'
]

for file in files:
    if os.path.exists(file):
        translate_file(file)

print("Done translating comments in python files.")
