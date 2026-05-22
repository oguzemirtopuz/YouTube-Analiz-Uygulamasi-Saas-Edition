import sys
with open('server.pyw', 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        if i >= 3950 and i <= 3980:
            print(f'{i+1}: {line.strip()}')
