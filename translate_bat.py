# -*- coding: utf-8 -*-
import os
import re
from deep_translator import GoogleTranslator

translator = GoogleTranslator(source='tr', target='en')

def translate_text(text):
    if not re.search(r'[a-zA-ZğüşiöçĞÜŞİÖÇ]', text):
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
        if line.strip().lower().startswith('echo') and 'off' not in line.strip().lower():
            text_part = line[line.lower().find('echo') + 4:].strip()
            if text_part and re.search(r'[a-zA-ZğüşiöçĞÜŞİÖÇ]', text_part):
                translated = translate_text(text_part)
                lines[i] = line[:line.lower().find('echo') + 4] + " " + translated

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

files = [
    'build.bat', 'deploy.bat', 'install.bat'
]

for file in files:
    if os.path.exists(file):
        translate_file(file)

print("Done translating BAT files.")
