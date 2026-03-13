from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os
import subprocess
import sys
import logging

app = Flask(__name__)
CORS(app)

# 使用绝对路径定位数据库文件
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, '4d_results.db')
CRAWLER_SECRET = os.environ.get('CRAWLER_SECRET', 'default-secret-change-me')

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection():
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logging.error(f"数据库连接失败: {e}")
        return None

def query_db(query, args=(), one=False):
    conn = get_db_connection()
    if not conn:
        return None if one else []
    cur = conn.cursor()
    try:
        cur.execute(query, args)
        rv = cur.fetchall()
        return (rv[0] if rv else None) if one else rv
    except sqlite3.Error as e:
        logging.error(f"查询失败: {e}")
        return None if one else []
    finally:
        conn.close()

def get_latest_draw_date(company):
    row = query_db(
        'SELECT draw_date FROM results WHERE company = ? ORDER BY draw_date DESC LIMIT 1',
        [company],
        one=True
    )
    return row['draw_date'] if row else None

@app.route('/api/company/<company>', methods=['GET'])
def get_full_data(company):
    logging.info(f"收到全量数据请求: {company}")
    today = datetime.now().strftime("%Y-%m-%d")
    rows = query_db(
        'SELECT id, type, number FROM results WHERE company = ? AND draw_date = ? ORDER BY id',
        [company, today]
    )
    if rows:
        target_date = today
    else:
        latest = get_latest_draw_date(company)
        if not latest:
            logging.warning(f"公司 {company} 无任何数据")
            return jsonify({
                'draw_date': '',
                'max_id': 0,
                'special': [],
                'consolation': [],
                'prize': []
            })
        target_date = latest
        rows = query_db(
            'SELECT id, type, number FROM results WHERE company = ? AND draw_date = ? ORDER BY id',
            [company, target_date]
        )
        if not rows:
            logging.error(f"公司 {company} 在日期 {target_date} 应有数据但查询为空")
            return jsonify({'draw_date': '', 'max_id': 0})

    result = {
        'draw_date': datetime.strptime(target_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
        'max_id': 0
    }
    max_id = 0
    for row in rows:
        t = row['type']
        num = row['number']
        result.setdefault(t, []).append(num)
        if row['id'] > max_id:
            max_id = row['id']
    result['max_id'] = max_id
    logging.info(f"返回 {company} 的数据，日期 {target_date}，max_id {max_id}")
    return jsonify(result)

@app.route('/api/company/<company>/latest', methods=['GET'])
def get_latest(company):
    after = request.args.get('after', 0, type=int)
    today = datetime.now().strftime("%Y-%m-%d")
    rows = query_db(
        'SELECT id, type, number FROM results WHERE company = ? AND draw_date = ? AND id > ? ORDER BY id',
        [company, today, after]
    )
    data = [{'id': r['id'], 'type': r['type'], 'number': r['number']} for r in rows] if rows else []
    return jsonify(data)

@app.route('/api/health', methods=['GET'])
def health_check():
    # 同时检查数据库文件是否存在，用于诊断
    db_exists = os.path.exists(DATABASE)
    return jsonify({'status': 'ok', 'database_exists': db_exists})

@app.route('/api/trigger-crawler', methods=['GET'])
def trigger_crawler():
    secret = request.args.get('secret')
    if secret != CRAWLER_SECRET:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        # 在子进程中运行爬虫，并传入相同的绝对路径环境变量（如果爬虫支持）
        # 注意：需要确保 crawler.py 也使用相同的 DATABASE 绝对路径
        # 这里我们通过修改环境变量传递给子进程（如果 crawler.py 读取 DB_PATH 环境变量）
        env = os.environ.copy()
        env['DB_PATH'] = DATABASE  # 如果 crawler.py 支持从环境变量读取，则传递
        result = subprocess.run([sys.executable, 'crawler.py'],
                                capture_output=True, text=True, timeout=300, env=env)
        return jsonify({
            'status': 'success',
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({'status': 'error', 'message': 'Crawler timed out'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 初始化数据库（在应用启动时运行）
def init_database():
    try:
        import database
        database.init_db()
        logging.info("数据库初始化成功")
    except Exception as e:
        logging.error(f"数据库初始化失败: {e}")

# 启动时初始化数据库
init_database()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
