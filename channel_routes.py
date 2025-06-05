# channel_routes.py: Slack風掲示板機能に関するルート・処理まとめ

from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime

# Blueprint作成
channel_bp = Blueprint('channel', __name__)

# 定数定義
DB_FILE = 'users.db'
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# DB接続関数
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# --- チャンネルページ表示＆投稿処理 ---
@channel_bp.route('/channels/<channel_name>', methods=['GET', 'POST'])
def channel_page(channel_name):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # 投稿処理
    if request.method == 'POST':
        content = request.form.get('content')
        is_anonymous = int(request.form.get('is_anonymous', 0))
        user_id = session['user_id']

        # 画像保存
        image = request.files.get('image')
        image_path = None
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            timestamp_str = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{user_id}_{timestamp_str}_{filename}"
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            image.save(save_path)
            image_path = filename

        # 投稿をDBに保存
        cursor.execute('''
            INSERT INTO posts (user_id, channel, content, image_path, is_anonymous)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, channel_name, content, image_path, is_anonymous))
        conn.commit()

    # 投稿一覧取得（新しい順）
    cursor.execute('''
        SELECT posts.*, users.full_name FROM posts
        JOIN users ON posts.user_id = users.id
        WHERE channel = ?
        ORDER BY timestamp DESC
    ''', (channel_name,))
    posts = cursor.fetchall()
    conn.close()

    return render_template('channel.html', channel=channel_name, posts=posts, user_id=session['user_id'])

# --- 投稿削除処理 ---
@channel_bp.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # 投稿情報取得
    cursor.execute('SELECT user_id, image_path FROM posts WHERE id = ?', (post_id,))
    post = cursor.fetchone()

    if post and post['user_id'] == session['user_id']:
        # 画像削除
        if post['image_path']:
            try:
                os.remove(os.path.join(UPLOAD_FOLDER, post['image_path']))
            except Exception as e:
                print(e)
        # 投稿削除
        cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
        conn.commit()

    conn.close()
    return redirect(request.referrer)