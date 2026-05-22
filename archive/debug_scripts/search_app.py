import sys
import re
import os

file_path = os.path.join(os.path.dirname(__file__), 'static', 'App.js')

with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()
    if 'send_report' in content or 'pdf' in content:
        matches = re.finditer(r'(.{0,100}send_report.{0,100})', content)
        for m in matches:
            print(m.group(1).replace('\n', ' '))
