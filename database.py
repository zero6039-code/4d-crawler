import sqlite3

def init_db():
    conn = sqlite3.connect('4d_results.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            type TEXT NOT NULL,
            number TEXT NOT NULL,
            draw_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized.")