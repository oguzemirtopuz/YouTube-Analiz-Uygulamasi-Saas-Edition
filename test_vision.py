import sqlite3, requests
conn=sqlite3.connect('channels.db')
c=conn.cursor()
c.execute("SELECT value FROM app_settings WHERE key='gemini_api_key'")
k = c.fetchone()[0]
p = {'contents': [{'parts': [{'text': 'Hello'}, {'inline_data': {'mime_type': 'image/jpeg', 'data': '/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCABkAGQDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAT/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFAEBAAAAAAAAAAAAAAAAAAAAAP/EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAMAwEAAhEDEQA/APQAAA//2Q=='}}]}]}
print('1.5-flash:', requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={k}', json=p).status_code)
print('1.5-pro:', requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={k}', json=p).status_code)
