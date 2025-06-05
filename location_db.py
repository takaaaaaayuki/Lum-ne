# location_db.py
import sqlite3
import os
import random
from datetime import datetime

# 位置情報データベースファイルパス
LOCATION_DB_FILE = 'location.db'

# データベース接続関数
def get_location_db_connection():
    conn = sqlite3.connect(LOCATION_DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# 位置情報テーブル初期化関数
def init_location_db():
    if not os.path.exists(LOCATION_DB_FILE):
        print("📍 位置情報データベースを新規作成します...")
    
    conn = get_location_db_connection()
    cursor = conn.cursor()
    
    # ユーザー位置情報テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_locations (
            user_id INTEGER PRIMARY KEY,
            latitude REAL,
            longitude REAL,
            is_sharing INTEGER DEFAULT 0,
            share_option TEXT DEFAULT 'friends',
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    # 友達関係テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_friends (
            user_id INTEGER,
            friend_id INTEGER,
            PRIMARY KEY (user_id, friend_id)
        );
    ''')
    
    conn.commit()
    conn.close()
    print("✅ 位置情報データベース初期化完了")

# 仮のユーザー位置データを追加する関数
def add_dummy_location_data(users_db_file):
    # 先にテーブルが存在することを確認
    init_location_db()

    # メインのユーザーデータベースからユーザー情報を取得
    # データベースが存在しない場合は作成する
    if not os.path.exists(users_db_file):
        print(f"⚠️ ユーザーデータベース {users_db_file} が存在しません。")
        return
        
    conn_users = sqlite3.connect(users_db_file)
    conn_users.row_factory = sqlite3.Row
    cursor_users = conn_users.cursor()
    
    # ユーザーテーブルが存在するか確認
    try:
        cursor_users.execute('SELECT id, full_name, campus, faculty, grade FROM users')
        users = cursor_users.fetchall()
    except sqlite3.OperationalError:
        print("⚠️ usersテーブルが存在しないか、必要なカラムがありません。")
        conn_users.close()
        return
    
    if not users:
        print("⚠️ ユーザーが存在しません。先にユーザーを作成してください。")
        conn_users.close()
        return
    
    # 位置情報データベースに接続
    conn_location = get_location_db_connection()
    cursor_location = conn_location.cursor()
    
    # 既存のデータをクリア（デモ用）
    cursor_location.execute('DELETE FROM user_locations')
    cursor_location.execute('DELETE FROM user_friends')
    
    # キャンパスの基準座標
    campuses = {
        "有明キャンパス": {"lat": 35.6372, "lng": 139.7915},
        "武蔵野キャンパス": {"lat": 35.7183, "lng": 139.5687},
        "本郷キャンパス": {"lat": 35.7130, "lng": 139.7627},
        "駒場キャンパス": {"lat": 35.6597, "lng": 139.6847}
    }
    
    # ユーザーごとにランダムな位置情報を生成
    for user in users:
        user_id = user['id']
        
        # sqlite3.Row オブジェクトは辞書のように ['key'] でアクセスするか
        # インデックスを使用してアクセスする必要がある
        try:
            campus = user['campus']
        except (IndexError, KeyError):
            campus = None  # カラムが存在しない場合
        
        # キャンパスの基準座標を取得（なければデフォルト値を使用）
        base_coords = campuses.get(campus, {"lat": 35.6812, "lng": 139.7671})
        
        # ランダムなオフセット（約500m以内の範囲）
        lat_offset = random.uniform(-0.004, 0.004)
        lng_offset = random.uniform(-0.004, 0.004)
        
        latitude = base_coords["lat"] + lat_offset
        longitude = base_coords["lng"] + lng_offset
        
        # デモ用にすべて「全員に共有」設定
        share_option = 'all'
        
        # 位置情報をデータベースに挿入
        cursor_location.execute('''
            INSERT INTO user_locations 
            (user_id, latitude, longitude, is_sharing, share_option, last_updated)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        ''', (user_id, latitude, longitude, 1, share_option))
        
        try:
            full_name = user['full_name']
        except (IndexError, KeyError):
            full_name = f'ユーザー{user_id}'
            
        print(f"📍 ユーザー {full_name} の位置情報を追加: ({latitude}, {longitude})")
    
    # ランダムな友達関係の生成
    all_user_ids = [user['id'] for user in users]
    
    # 各ユーザーにランダムな友達を割り当て
    for user_id in all_user_ids:
        # ランダムに1〜5人の友達を選択
        num_friends = min(random.randint(1, 5), len(all_user_ids) - 1)
        potential_friends = [id for id in all_user_ids if id != user_id]
        
        if potential_friends:
            friends = random.sample(potential_friends, num_friends)
            
            for friend_id in friends:
                cursor_location.execute('''
                    INSERT OR IGNORE INTO user_friends (user_id, friend_id)
                    VALUES (?, ?)
                ''', (user_id, friend_id))
                
                # 双方向の友達関係（AがBの友達なら、BもAの友達）
                cursor_location.execute('''
                    INSERT OR IGNORE INTO user_friends (user_id, friend_id)
                    VALUES (?, ?)
                ''', (friend_id, user_id))
    
    conn_location.commit()
    conn_location.close()
    conn_users.close()
    
    print(f"✅ {len(users)}人のユーザーに仮の位置情報を追加しました")
    print("✅ ランダムな友達関係を生成しました")

# スタンドアロンで実行する場合
if __name__ == "__main__":
    init_location_db()
    add_dummy_location_data('users.db')