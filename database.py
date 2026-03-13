import sqlite3
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 获取当前文件所在目录的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '4d_results.db')

def init_db():
    """初始化数据库表，如果表已存在则跳过"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # 创建主表
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
        
        # 为常用查询字段创建索引，大幅提升查询速度
        c.execute('CREATE INDEX IF NOT EXISTS idx_company_drawdate ON results (company, draw_date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_draw_date ON results (draw_date)')
        
        conn.commit()
        logging.info(f"数据库初始化成功，路径: {DB_PATH}")
    except sqlite3.Error as e:
        logging.error(f"数据库初始化失败: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    init_db()
