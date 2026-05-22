import sys
with open('static/App.js', 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        if 'email' in line or 'send_' in line or 'pdf' in line or 'progress' in line:
            print(f'{i+1}: {line.strip()}')
