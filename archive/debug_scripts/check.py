import sqlite3
import base64
conn = sqlite3.connect('channels.db')
c = conn.cursor()
c.execute("SELECT value FROM app_settings WHERE key='gemini_api_key'")
row = c.fetchone()
print("DB KEY:", bool(row and row[0]))
if row: print("Key preview:", row[0][:5] if row[0] else 'Empty')
