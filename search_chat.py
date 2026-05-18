import sys
import codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
with open('server.pyw', 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        if 'def api_chat' in line or 'def chat' in line or '/api/chat' in line:
            print(f'{i+1}: {line.strip()}')
