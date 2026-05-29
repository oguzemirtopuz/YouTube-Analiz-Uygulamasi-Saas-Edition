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
        if '<!--' in line and '-->' in line:
            start = line.find('<!--') + 4
            end = line.find('-->')
            comment_text = line[start:end].strip()
            if comment_text:
                translated = translate_text(comment_text)
                lines[i] = line[:start-4] + f"<!-- {translated} -->" + line[end+3:]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

files = [
    'chrome_extension/popup.html',
]

for file in files:
    file = file.replace('/', os.sep)
    if os.path.exists(file):
        translate_file(file)

print("Done translating HTML comments.")
