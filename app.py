from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DB_FILE = 'users.db'
TIMETABLE_DB = 'timetable.db'
POSTS_DB = 'posts.db'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# アップロードフォルダがなければ作成する
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ユーザーデータベースの初期化
def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                age INTEGER,
                grade TEXT,
                gender TEXT,
                university TEXT,
                faculty TEXT,
                campus TEXT
            );
        ''')
        conn.commit()
        conn.close()
        print("✅ ユーザーデータベース作成完了")

# 時間割専用データベースの初期化
def init_timetable_db():
    if not os.path.exists(TIMETABLE_DB):
        conn = sqlite3.connect(TIMETABLE_DB)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE timetable (
                user_id INTEGER,
                cell_id TEXT,
                lecture_name TEXT,
                lecture_room TEXT,
                lecture_color TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, cell_id)
            );
        ''')
        conn.commit()
        conn.close()
        print("✅ 時間割データベース作成完了")

# 投稿専用データベースの初期化（commentsテーブルを追加）
def init_posts_db():
    if not os.path.exists(POSTS_DB):
        conn = sqlite3.connect(POSTS_DB)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                photo TEXT,
                title TEXT NOT NULL,
                heart_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
        ''')
        # コメントテーブルの作成
        cursor.execute('''
            CREATE TABLE comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                comment TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(post_id) REFERENCES posts(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
        ''')
        conn.commit()
        conn.close()
        print("✅ 投稿データベース作成完了")

# ユーザーデータベース接続関数
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ルート定義（元のコードそのまま）
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        hashed_password = generate_password_hash(data['password'])
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (email, password, full_name, age, grade, gender, university, faculty, campus)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['email'], hashed_password, data['full_name'], data['age'], data['grade'],
            data['gender'], data['university'], data['faculty'], data['campus']
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/api/status')
def api_status():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT facility_name, status, updated_at 
        FROM facility_status 
        ORDER BY updated_at DESC 
        LIMIT 10
    ''')
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append({
            'facility_name': row['facility_name'],
            'status': row['status'],
            'updated_at': row['updated_at']
        })
    return jsonify(result)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        data = request.form
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (data['email'],))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user['password'], data['password']):
            session['user_id'] = user['id']
            session['university'] = user['university']
            return redirect(url_for('dashboard'))
        else:
            error = 'メールアドレスまたはパスワードが正しくありません。'
    return render_template('login.html', error=error)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/timetable')
def timetable():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('timetable.html')

@app.route('/place')
def place():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT facility_name, status, updated_at 
        FROM facility_status 
        ORDER BY updated_at DESC 
        LIMIT 10
    ''')
    records = cursor.fetchall()
    conn.close()
    return render_template('place.html', records=records)


@app.route('/page3')
def page3():
    return render_template('page3.html')

@app.route('/page4')
def page4():
    return render_template('page4.html')

@app.route('/page5')
def page5():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # ログインユーザーの情報を取得
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT university, campus FROM users WHERE id = ?', (session['user_id'],))
    user_info = cursor.fetchone()
    
    if not user_info:
        return redirect(url_for('login'))
    
    university = user_info['university']
    campus = user_info['campus']
    
    # ユーザーのキャンパス周辺のスポットを取得
    cursor.execute('''
        SELECT * FROM entertainment_spots 
        WHERE (university = ? AND campus = ?) OR university = 'all'
        ORDER BY category, rating DESC
    ''', (university, campus))
    
    spots = cursor.fetchall()
    conn.close()
    
    # スポットのfeatures文字列をリストに変換
    for i, spot in enumerate(spots):
        if spot['features']:
            spots[i] = dict(spot)  # sqliteのRowオブジェクトを通常の辞書に変換
            spots[i]['feature_list'] = spot['features'].split(',')
    
    return render_template('page5.html', spots=spots, user_campus=campus, user_university=university)

@app.route('/map')
def map_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # ユーザー情報を取得
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return redirect(url_for('login'))
    
    return render_template('map.html', 
                          user_id=user['id'],
                          user_name=user['full_name'], 
                          user_faculty=user['faculty'],
                          user_grade=user['grade'],
                          user_campus=user['campus'])

# URLルーティングのエイリアス
@app.route('/map_page')
def map_page_alias():
    return map_page()

# --- 位置情報を更新するAPI ---
@app.route('/api/update_location', methods=['POST'])
def update_location():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'ログインが必要です'})
    
    data = request.json
    user_id = session['user_id']
    
    try:
        conn = get_location_db_connection()
        cursor = conn.cursor()
        
        # 位置情報を更新
        cursor.execute('''
            INSERT OR REPLACE INTO user_locations 
            (user_id, latitude, longitude, is_sharing, last_updated) 
            VALUES (?, ?, ?, 1, datetime('now'))
        ''', (user_id, data['latitude'], data['longitude']))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"位置情報更新エラー: {e}")
        return jsonify({'success': False, 'error': str(e)})

# --- 位置情報共有を停止するAPI ---
@app.route('/api/stop_location_sharing', methods=['POST'])
def stop_location_sharing():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'ログインが必要です'})
    
    user_id = session['user_id']
    
    try:
        conn = get_location_db_connection()
        cursor = conn.cursor()
        
        # is_sharingを0に設定
        cursor.execute('''
            UPDATE user_locations 
            SET is_sharing = 0 
            WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"位置情報共有停止エラー: {e}")
        return jsonify({'success': False, 'error': str(e)})

# --- 設定を保存するAPI ---
@app.route('/api/save_location_settings', methods=['POST'])
def save_location_settings():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'ログインが必要です'})
    
    data = request.json
    user_id = session['user_id']
    
    try:
        conn = get_location_db_connection()
        cursor = conn.cursor()
        
        # 設定を更新
        cursor.execute('''
            INSERT OR REPLACE INTO user_locations 
            (user_id, is_sharing, share_option, latitude, longitude, last_updated) 
            VALUES (
                ?, ?, ?, 
                COALESCE((SELECT latitude FROM user_locations WHERE user_id = ?), 0),
                COALESCE((SELECT longitude FROM user_locations WHERE user_id = ?), 0),
                datetime('now')
            )
        ''', (user_id, 1 if data['is_sharing'] else 0, data['share_option'], user_id, user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"設定保存エラー: {e}")
        return jsonify({'success': False, 'error': str(e)})

# --- 設定を取得するAPI ---
@app.route('/api/get_location_settings')
def get_location_settings():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'ログインが必要です'})
    
    user_id = session['user_id']
    
    try:
        conn = get_location_db_connection()
        cursor = conn.cursor()
        
        # 設定を取得
        cursor.execute('''
            SELECT is_sharing, share_option
            FROM user_locations
            WHERE user_id = ?
        ''', (user_id,))
        
        settings = cursor.fetchone()
        conn.close()
        
        if settings:
            return jsonify({
                'success': True,
                'is_sharing': bool(settings['is_sharing']),
                'share_option': settings['share_option']
            })
        else:
            # デフォルト値を返す
            return jsonify({
                'success': True,
                'is_sharing': False,
                'share_option': 'friends'
            })
    except Exception as e:
        print(f"設定取得エラー: {e}")
        return jsonify({'success': False, 'error': str(e)})

# --- 他のユーザーの位置情報を取得するAPI ---
@app.route('/api/get_user_locations')
def get_user_locations():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'ログインが必要です'})
    
    user_id = session['user_id']
    filter_type = request.args.get('filter', 'all')
    
    try:
        # ユーザー情報を取得するためのメインDB接続
        conn_users = get_db_connection()
        cursor_users = conn_users.cursor()
        
        # 位置情報を取得するための位置情報DB接続
        conn_location = get_location_db_connection()
        cursor_location = conn_location.cursor()
        
        # 現在のユーザー情報を取得
        cursor_users.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        current_user = cursor_users.fetchone()
        
        if not current_user:
            return jsonify({'success': False, 'error': '現在のユーザー情報が見つかりません'})
        
        # 位置情報を共有しているすべてのユーザーIDを取得
        cursor_location.execute('SELECT user_id FROM user_locations WHERE is_sharing = 1')
        shared_user_ids = [row['user_id'] for row in cursor_location.fetchall()]
        
        if not shared_user_ids:
            return jsonify({'success': True, 'users': []})
        
        # フィルタリング条件に基づいて表示するユーザーを絞り込む
        filtered_user_ids = shared_user_ids
        
        if filter_type == 'friends':
            cursor_location.execute('SELECT friend_id FROM user_friends WHERE user_id = ?', (user_id,))
            friend_ids = [row['friend_id'] for row in cursor_location.fetchall()]
            filtered_user_ids = [uid for uid in shared_user_ids if uid in friend_ids]
        
        elif filter_type == 'same-faculty':
            cursor_users.execute('''
                SELECT id FROM users 
                WHERE faculty = ? AND university = ?
            ''', (current_user['faculty'], current_user['university']))
            same_faculty_ids = [row['id'] for row in cursor_users.fetchall()]
            filtered_user_ids = [uid for uid in shared_user_ids if uid in same_faculty_ids]
        
        elif filter_type == 'same-grade':
            cursor_users.execute('''
                SELECT id FROM users 
                WHERE grade = ? AND university = ?
            ''', (current_user['grade'], current_user['university']))
            same_grade_ids = [row['id'] for row in cursor_users.fetchall()]
            filtered_user_ids = [uid for uid in shared_user_ids if uid in same_grade_ids]
        
        # 自分自身を除外
        if user_id in filtered_user_ids:
            filtered_user_ids.remove(user_id)
        
        if not filtered_user_ids:
            return jsonify({'success': True, 'users': []})
        
        # ユーザー情報と位置情報を結合
        result = []
        for uid in filtered_user_ids:
            # ユーザー情報を取得
            cursor_users.execute('SELECT * FROM users WHERE id = ?', (uid,))
            user = cursor_users.fetchone()
            
            if not user:
                continue
            
            # 位置情報を取得
            cursor_location.execute('SELECT * FROM user_locations WHERE user_id = ?', (uid,))
            location = cursor_location.fetchone()
            
            if not location:
                continue
            
            # 共有設定に基づくアクセス権チェック
            if location['share_option'] == 'all':
                pass  # 全員に共有
            elif location['share_option'] == 'friends':
                cursor_location.execute('''
                    SELECT COUNT(*) as is_friend FROM user_friends 
                    WHERE user_id = ? AND friend_id = ?
                ''', (uid, user_id))
                if not cursor_location.fetchone()['is_friend']:
                    continue  # 友達でないため表示しない
            elif location['share_option'] == 'faculty':
                if user['faculty'] != current_user['faculty'] or user['university'] != current_user['university']:
                    continue  # 同じ学部でないため表示しない
            elif location['share_option'] == 'grade':
                if user['grade'] != current_user['grade'] or user['university'] != current_user['university']:
                    continue  # 同じ学年でないため表示しない
            
            # ユーザー情報と位置情報を結合して結果に追加
            result.append({
                'id': user['id'],
                'name': user['full_name'],
                'faculty': user['faculty'],
                'grade': user['grade'],
                'campus': user['campus'],
                'latitude': location['latitude'],
                'longitude': location['longitude'],
                'last_updated': location['last_updated']
            })
        
        conn_users.close()
        conn_location.close()
        
        return jsonify({'success': True, 'users': result})
    
    except Exception as e:
        print(f"ユーザー位置情報取得エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

# --- 友達追加・削除のAPI ---
@app.route('/api/toggle_friend', methods=['POST'])
def toggle_friend():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'ログインが必要です'})
    
    user_id = session['user_id']
    friend_id = request.json.get('friend_id')
    
    if user_id == friend_id:
        return jsonify({'success': False, 'error': '自分自身を友達に追加することはできません'})
    
    try:
        conn = get_location_db_connection()
        cursor = conn.cursor()
        
        # 友達関係が既に存在するか確認
        cursor.execute('SELECT * FROM user_friends WHERE user_id = ? AND friend_id = ?', 
                      (user_id, friend_id))
        exists = cursor.fetchone()
        
        if exists:
            # 友達関係を削除
            cursor.execute('DELETE FROM user_friends WHERE user_id = ? AND friend_id = ?', 
                          (user_id, friend_id))
            cursor.execute('DELETE FROM user_friends WHERE user_id = ? AND friend_id = ?', 
                          (friend_id, user_id))
            action = 'removed'
        else:
            # 友達関係を追加
            cursor.execute('INSERT INTO user_friends (user_id, friend_id) VALUES (?, ?)', 
                          (user_id, friend_id))
            cursor.execute('INSERT INTO user_friends (user_id, friend_id) VALUES (?, ?)', 
                          (friend_id, user_id))
            action = 'added'
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'action': action})
    except Exception as e:
        print(f"友達リスト更新エラー: {e}")
        return jsonify({'success': False, 'error': str(e)})

# 以下、投稿機能の追加（マイページ機能は削除）

# タイムライン（全ユーザーの投稿を新しい順に表示） → placeとしても利用可能
@app.route('/timeline')
def timeline():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(POSTS_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM posts 
        ORDER BY created_at DESC
    ''')
    posts = cursor.fetchall()
    conn.close()
    return render_template('timeline.html', posts=posts)

# 投稿フォームの表示および投稿処理
@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form.get('title')
        photo = request.files.get('photo')
        if photo:
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        else:
            photo_path = ""
        user_id = session.get('user_id')
        conn = sqlite3.connect(POSTS_DB)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO posts (user_id, photo, title) VALUES (?, ?, ?)
        ''', (user_id, photo_path, title))
        conn.commit()
        conn.close()
        flash("投稿が完了しました。")
        return redirect(url_for('timeline'))
    return render_template('add_post.html')

# 投稿詳細（個別投稿ページ＋匿名コメント機能）
@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post_detail(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(POSTS_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if request.method == 'POST':
        comment_text = request.form.get('comment')
        # 匿名コメントとして user_id を 0 で保存
        if comment_text:
            cursor.execute('''
                INSERT INTO comments (post_id, user_id, comment)
                VALUES (?, ?, ?)
            ''', (post_id, 0, comment_text))
            cursor.execute('''
                UPDATE posts SET comment_count = comment_count + 1
                WHERE id = ?
            ''', (post_id,))
            conn.commit()
    cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
    post = cursor.fetchone()
    cursor.execute('''
        SELECT * FROM comments 
        WHERE post_id = ?
        ORDER BY created_at ASC
    ''', (post_id,))
    comments = cursor.fetchall()
    conn.close()
    return render_template('post_detail.html', post=post, comments=comments)

# 以下は時間割のAJAXエンドポイント（元のコードそのまま）
@app.route('/update_lecture', methods=['POST'])
def update_lecture():
    if 'user_id' not in session:
        return jsonify(success=False), 401
    data = request.get_json()
    cell_id = data.get("cellId")
    lecture_name = data.get("lectureName")
    lecture_room = data.get("lectureRoom")
    lecture_color = data.get("lectureColor")
    user_id = session.get('user_id')
    if not cell_id:
        return jsonify(success=False), 400
    try:
        conn = sqlite3.connect(TIMETABLE_DB)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO timetable (user_id, cell_id, lecture_name, lecture_room, lecture_color)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, cell_id, lecture_name, lecture_room, lecture_color))
        conn.commit()
        conn.close()
        return jsonify(success=True)
    except Exception as e:
        print(e)
        return jsonify(success=False), 500

@app.route('/get_all_lectures', methods=['GET'])
def get_all_lectures():
    if 'user_id' not in session:
        return jsonify(success=False), 401
    user_id = session.get('user_id')
    try:
        conn = sqlite3.connect(TIMETABLE_DB)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT cell_id, lecture_name, lecture_room, lecture_color 
            FROM timetable 
            WHERE user_id = ?
        ''', (user_id,))
        lectures = cursor.fetchall()
        conn.close()
        lectures_list = []
        for lecture in lectures:
            lectures_list.append({
                'cell_id': lecture[0],
                'lecture_name': lecture[1],
                'lecture_room': lecture[2],
                'lecture_color': lecture[3]
            })
        return jsonify(success=True, lectures=lectures_list)
    except Exception as e:
        print(e)
        return jsonify(success=False), 500
    
    
def create_posts_table_in_users_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            channel TEXT NOT NULL,
            content TEXT,
            image_path TEXT,
            is_anonymous INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    ''')
    conn.commit()
    conn.close()
    print("✅ users.dbにpostsテーブルを追加完了")


@app.route('/update_all_lectures', methods=['POST'])
def update_all_lectures():
    if 'user_id' not in session:
        return jsonify(success=False), 401
    user_id = session.get('user_id')
    data = request.get_json()
    lectures = data.get("lectures", [])
    try:
        conn = sqlite3.connect(TIMETABLE_DB)
        cursor = conn.cursor()
        for lecture in lectures:
            cell_id = lecture.get("cell_id")
            lecture_name = lecture.get("lecture_name")
            lecture_room = lecture.get("lecture_room")
            lecture_color = lecture.get("lecture_color")
            cursor.execute('''
                INSERT OR REPLACE INTO timetable (user_id, cell_id, lecture_name, lecture_room, lecture_color)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, cell_id, lecture_name, lecture_room, lecture_color))
        conn.commit()
        conn.close()
        return jsonify(success=True)
    except Exception as e:
        print(e)
        return jsonify(success=False), 500
    

from booktrade import booktrade_bp
from channel_routes import channel_bp  # ← 追加！

app.register_blueprint(booktrade_bp, url_prefix='/booktrade')
app.register_blueprint(channel_bp)  # ← 追加！

def create_entertainment_spots_table():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entertainment_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            rating REAL,
            university TEXT,
            campus TEXT,
            features TEXT
        );
    ''')
    conn.commit()
    conn.close()
    print(":white_check_mark: users.dbにentertainment_spotsテーブルを追加完了")
    
@app.route('/update', methods=['GET', 'POST'])
def update_status_page():
    error = ''
    if request.method == 'POST':
        facility_name = request.form.get('facility_name')
        status = request.form.get('status')
        password = request.form.get('password')

        # 簡易パスワードチェック（例: admin123）
        if password != 'admin123':
            error = "パスワードが違います"
            return render_template('update.html', error=error)

        # データベース保存
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO facility_status (facility_name, status, updated_at)
            VALUES (?, ?, datetime('now'))
        ''', (facility_name, status))
        conn.commit()
        conn.close()

        return redirect('/place')

    return render_template('update.html', error=error)

def create_facility_status_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facility_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_name TEXT,
            status TEXT,
            updated_at TEXT
        );
    ''')
    conn.commit()
    conn.close()
    print("✅ facility_status テーブル作成済み")

    

if __name__ == '__main__':
    print("🔥 アプリ起動準備中...")
    init_db()
    init_timetable_db()
    init_posts_db()
    create_posts_table_in_users_db()  # ← これ追加！
    create_entertainment_spots_table()
    create_facility_status_table()  # ← これを追加！
    print("🟢 Flask起動中: http://localhost:5000")
    app.run(debug=True)
