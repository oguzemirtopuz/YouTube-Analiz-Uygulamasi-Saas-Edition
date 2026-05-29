import re

with open('Start-YouTubeAnalyzer.ps1', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

text = re.sub(r'Python bulunamad.*?downloads', 'Python not found!`n`nPlease install Python: https://python.org/downloads', text)
text = re.sub(r'server.py bulunamad.*?\$serverPath', 'server.py not found!`n`nFile path: $serverPath', text)
text = text.replace('YouTube Analiz Pro', 'YouTube Analyzer Pro')
text = text.replace('# Python komutunu bul', '# Find Python command')
text = re.sub(r'# Server.py kontrol.*', '# Check server.py', text)
text = re.sub(r'# Uygulamay.*', '# Start application (invisible)', text)

with open('Start-YouTubeAnalyzer.ps1', 'w', encoding='utf-8') as f:
    f.write(text)
