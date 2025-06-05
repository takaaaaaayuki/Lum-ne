# booktrade/models.py
# DBの初期テーブル作成用関数例
def create_books_table(mysql):
    cur = mysql.connection.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        author VARCHAR(255) NOT NULL,
        category VARCHAR(255),
        price DECIMAL(10,2),
        description TEXT,
        image VARCHAR(255),
        university VARCHAR(255) NOT NULL,
        seller_id INT NOT NULL,
        status ENUM('販売中', '売り切れ') DEFAULT '販売中',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    mysql.connection.commit()
    cur.close()

def create_messages_table(mysql):
    cur = mysql.connection.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INT AUTO_INCREMENT PRIMARY KEY,
        chat_id INT NOT NULL,
        sender_id INT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    mysql.connection.commit()
    cur.close()
