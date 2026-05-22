import sys
with open('server.pyw', 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        if i >= 3920 and i <= 3950:
            print(f'{i+1}: {line.strip()}')
