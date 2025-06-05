from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime

# Blueprint の作成
akijyoukyou_bp = Blueprint('akijyoukyou', __name__, template_folder='templates')

DB_FILE_FACILITY = 'facility_status.db'
PASSWORD = '123'  # 更新パスワード

# DB 接続関数
def get_db_connection():
    conn = sqlite3.connect(DB_FILE_FACILITY)
    conn.row_factory = sqlite3.Row
    return conn

# DB 初期化
def init_db_facility():
    conn = get_db_connection()
    cursor = conn.cursor()
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
    print("✅ 施設データベース初期化完了")

# 施設情報取得
def get_facility_status():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM facility_status ORDER BY updated_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

# 施設状況更新
def update_facility_status(facility_name, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE facility_status
        SET status = ?, updated_at = ?
        WHERE facility_name = ?
    ''', (status, datetime.now(), facility_name))
    conn.commit()
    conn.close()

# 施設状況ページ
@akijyoukyou_bp.route('/akijyoukyou')
def index():
    return render_template('index.html')

# API: 施設状況取得
@akijyoukyou_bp.route('/api/status', methods=['GET'])
def get_status():
    status_data = get_facility_status()
    return jsonify([dict(row) for row in status_data])

# 施設状況更新ページ
@akijyoukyou_bp.route('/update', methods=['GET', 'POST'])
def update():
    error = ''
    if request.method == 'POST':
        password = request.form['password']
        if password == PASSWORD:  # パスワード確認
            facility_name = request.form['facility_name']
            status = request.form['status']
            update_facility_status(facility_name, status)
            return redirect(url_for('akijyoukyou.index'))
        else:
            error = 'パスワードが間違っています。'
    return render_template('update.html', error=error)

# 初回起動時に DB 初期化
init_db_facility()
