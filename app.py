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

def normalize_date(date_str):
    """
    将输入的日期字符串统一转换为 YYYY-MM-DD 格式。
    支持 dd-mm-yyyy 和 yyyy-mm-dd 两种格式。
    如果无法解析，返回原字符串。
    """
    if not date_str:
        return date_str
    # 尝试解析为 dd-mm-yyyy
    try:
        d = datetime.strptime(date_str, "%d-%m-%Y")
        return d.strftime("%Y-%m-%d")
    except ValueError:
        pass
    # 尝试解析为 yyyy-mm-dd
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return date_str  # 已经是正确格式
    except ValueError:
        logging.warning(f"无法解析的日期格式: {date_str}")
        return date_str

def format_date_for_display(ymd_date):
    """将 YYYY-MM-DD 转换为 DD-MM-YYYY 用于前端显示"""
    if not ymd_date:
        return ''
    try:
        d = datetime.strptime(ymd_date, "%Y-%m-%d")
        return d.strftime("%d-%m-%Y")
    except ValueError:
        return ymd_date

def get_latest_draw_date(company):
    """获取该公司最新有数据的日期（始终返回 YYYY-MM-DD 格式）"""
    row = query_db(
        'SELECT draw_date FROM results WHERE company = ? ORDER BY draw_date DESC LIMIT 1',
        [company],
        one=True
    )
    if row:
        raw_date = row['draw_date']
        return normalize_date(raw_date)  # 统一格式
    return None

@app.route('/api/company/<company>', methods=['GET'])
def get_full_data(company):
    logging.info(f"收到全量数据请求: {company}")
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 尝试获取当天数据
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
        target_date = latest  # 此时已为 YYYY-MM-DD 格式
        rows = query_db(
            'SELECT id, type, number FROM results WHERE company = ? AND draw_date = ? ORDER BY id',
            [company, target_date]
        )
        if not rows:
            logging.error(f"公司 {company} 在日期 {target_date} 应有数据但查询为空")
            return jsonify({'draw_date': '', 'max_id': 0})

    result = {
        'draw_date': format_date_for_display(target_date),  # 转换为前端显示格式
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
    db_exists = os.path.exists(DATABASE)
    return jsonify({'status': 'ok', 'database_exists': db_exists})

@app.route('/api/trigger-crawler', methods=['GET'])
def trigger_crawler():
    secret = request.args.get('secret')
    if secret != CRAWLER_SECRET:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        env = os.environ.copy()
        env['DB_PATH'] = DATABASE
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

@app.route('/api/debug/db', methods=['GET'])
def debug_db():
    """调试接口：返回数据库状态和第一条数据"""
    result = {
        'database_path': DATABASE,
        'file_exists': os.path.exists(DATABASE),
        'tables': [],
        'sample_data': None,
        'error': None
    }
    if not result['file_exists']:
        return jsonify(result)
    
    try:
        conn = get_db_connection()
        if conn is None:
            result['error'] = '无法连接数据库'
            return jsonify(result)
        
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        result['tables'] = [row[0] for row in cur.fetchall()]
        
        cur.execute("SELECT * FROM results LIMIT 1")
        row = cur.fetchone()
        if row:
            result['sample_data'] = dict(row)
        conn.close()
    except Exception as e:
        result['error'] = str(e)
    return jsonify(result)

# 初始化数据库（在应用启动时运行）
def init_database():
    try:
        import database
        database.init_db()
        logging.info("数据库初始化成功")
    except Exception as e:
        logging.error(f"数据库初始化失败: {e}")

init_database()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
