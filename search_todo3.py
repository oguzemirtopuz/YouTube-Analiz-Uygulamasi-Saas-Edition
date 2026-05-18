import sys
import codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
with open('static/App.js', 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        if 'TODO' in line:
            print(f'{i+1}: {line.strip()}')
with open('static/App.css', 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        if 'TODO' in line:
            print(f'{i+1}: {line.strip()}')
