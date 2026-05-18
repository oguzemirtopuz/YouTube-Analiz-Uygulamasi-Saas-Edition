import sys
with open('server.pyw', 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        if 'def ' in line and ('analyze' in line or 'video' in line):
            print(f'{i+1}: {line.strip()}')
