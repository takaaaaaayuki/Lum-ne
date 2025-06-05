# booktrade/__init__.py
import sqlite3
import os
from flask import Blueprint, current_app, g

booktrade_bp = Blueprint('booktrade', __name__, template_folder='templates', static_folder='static')

# booktrade.db はこのファイルのあるディレクトリ内に作成する
BOOKTRADE_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'booktrade.db')

def get_db():
    if 'booktrade_db' not in g:
        g.booktrade_db = sqlite3.connect(BOOKTRADE_DB)
        g.booktrade_db.row_factory = sqlite3.Row
    return g.booktrade_db

def close_db(e=None):
    db = g.pop('booktrade_db', None)
    if db is not None:
        db.close()

# アプリ初回リクエスト時に DB を初期化する（schema.sql の内容を実行）
@booktrade_bp.before_app_request
def init_booktrade_db():
    db = get_db()
    with booktrade_bp.open_resource('schema.sql', mode='r') as f:
        db.executescript(f.read())
    db.commit()


@booktrade_bp.teardown_app_request
def teardown_db(exception):
    close_db()

from . import routes
