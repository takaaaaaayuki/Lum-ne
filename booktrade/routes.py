# booktrade/routes.py
import os
from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from . import booktrade_bp, get_db

# 本一覧ページ（/booktrade/）
@booktrade_bp.route('/')
def book_list():
    # session からユーザーの大学情報を取得する
    university = session.get('university')
    if not university:
        flash('ログインが必要である')
        return redirect(url_for('login'))
    db = get_db()
    cursor = db.execute("SELECT * FROM books WHERE university = ?", (university,))
    books = cursor.fetchall()
    return render_template('book_list.html', books=books)

# 本の詳細ページ（/booktrade/detail/<book_id>）
@booktrade_bp.route('/detail/<int:book_id>')
def book_detail(book_id):
    db = get_db()
    cursor = db.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    if not book:
        flash('該当する本が存在しない')
        return redirect(url_for('booktrade.book_list'))
    return render_template('book_detail.html', book=book)

# 本の出品ページ（/booktrade/sell）
@booktrade_bp.route('/sell', methods=['GET', 'POST'])
def sell_book():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        category = request.form.get('category')
        price = request.form.get('price')
        description = request.form.get('description')
        file = request.files.get('image')
        filename = None
        if file:
            filename = secure_filename(file.filename)
            upload_path = os.path.join('static', 'images', filename)
            file.save(upload_path)
        university = session.get('university')
        seller_id = session.get('user_id')
        db = get_db()
        db.execute("""
            INSERT INTO books (title, author, category, price, description, image, university, seller_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, '販売中')
        """, (title, author, category, price, description, filename, university, seller_id))
        db.commit()
        flash('本が出品された')
        return redirect(url_for('booktrade.book_list'))
    return render_template('sell_book.html')

# ユーザーマイページ（/booktrade/my_page）
@booktrade_bp.route('/my_page')
def my_page():
    user_id = session.get('user_id')
    if not user_id:
        flash('ログインが必要である')
        return redirect(url_for('login'))
    db = get_db()
    cursor = db.execute("SELECT * FROM books WHERE seller_id = ?", (user_id,))
    user_books = cursor.fetchall()
    cursor = db.execute("SELECT * FROM messages WHERE sender_id = ? OR sender_id = ? ORDER BY created_at DESC", (user_id, user_id))
    messages = cursor.fetchall()
    return render_template('my_page.html', books=user_books, messages=messages)

# 取引メッセージページ（/booktrade/messages/<chat_id>）
@booktrade_bp.route('/messages/<int:chat_id>', methods=['GET', 'POST'])
def messages(chat_id):
    db = get_db()
    if request.method == 'POST':
        content = request.form.get('message')
        user_id = session.get('user_id')
        db.execute("INSERT INTO messages (chat_id, sender_id, content) VALUES (?, ?, ?)", (chat_id, user_id, content))
        db.commit()
    cursor = db.execute("SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at ASC", (chat_id,))
    chat_messages = cursor.fetchall()
    return render_template('messages.html', messages=chat_messages)
