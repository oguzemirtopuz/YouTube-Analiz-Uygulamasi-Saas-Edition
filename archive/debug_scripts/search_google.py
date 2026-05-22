import sys
import codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
with open('static/App.js', 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        if 'google' in line.lower() or 'oauth' in line.lower() or 'login' in line.lower():
            print(f'{i+1}: {line.strip()}')
