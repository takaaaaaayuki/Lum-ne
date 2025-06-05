import sqlite3
from datetime import datetime

DB_FILE = 'facility_status.db'

# DB 接続関数
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# 初期データ登録 (テーブル作成)
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # テーブル作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facility_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_name TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 初期データの挿入
    facilities = ['食堂', '図書館', '自習室']
    for facility in facilities:
        cursor.execute('''
            INSERT OR IGNORE INTO facility_status (facility_name, status, updated_at)
            VALUES (?, ?, ?)
        ''', (facility, '空き', datetime.now()))

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ データベースと初期データ作成完了")
