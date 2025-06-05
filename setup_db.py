import sqlite3
from datetime import datetime

DB_FILE = 'users.db'  # app.pyと同じDBを使用

def init_facility_status_table():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facility_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_name TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    ''')
    conn.commit()
    conn.close()
    print("✅ facility_status テーブル作成完了")

if __name__ == '__main__':
    init_facility_status_table()
