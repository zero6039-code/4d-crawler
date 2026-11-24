from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os
import re
import logging

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["https://my4d.vercel.app"]}}, methods=["GET"])

# 可选限流：未安装 flask-limiter 时不阻断启动
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    Limiter(app=app, key_func=get_remote_address, default_limits=["120 per minute"])
except ImportError:
    pass

# 使用绝对路径定位数据库文件
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, '4d_results.db')
COMPANY_RE = re.compile(r'^[a-z0-9_]{1,40}$')
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

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
    支持 dd-mm-yyyy 和 yyyy-mm-dd 两种格式，自动去除首尾空格。
    如果无法解析，返回原字符串并记录警告。
    """
    if not date_str:
        return date_str
    original = date_str
    date_str = date_str.strip()
    # 尝试解析为 dd-mm-yyyy
    try:
        d = datetime.strptime(date_str, "%d-%m-%Y")
        normalized = d.strftime("%Y-%m-%d")
        logging.debug(f"日期标准化: {original} -> {normalized}")
        return normalized
    except ValueError:
        pass
    # 尝试解析为 yyyy-mm-dd
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        logging.debug(f"日期已经是标准格式: {original}")
        return date_str
    except ValueError:
        logging.warning(f"无法解析的日期格式: {original}")
        return original

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
        normalized = normalize_date(raw_date)
        logging.info(f"公司 {company} 最新日期: {raw_date} -> 标准化为 {normalized}")
        return normalized
    return None

def valid_company(company):
    """公司名白名单校验，阻断异常路径参数"""
    if not COMPANY_RE.match(company):
        abort(400, "bad company")
    return company

@app.after_request
def sec_headers(r):
    r.headers["X-Content-Type-Options"] = "nosniff"
    return r

@app.route('/api/company/<company>', methods=['GET'])
def get_full_data(company):
    """
    全量接口：
    - 优先返回当天数据，若无则返回最近一期数据。
    - 返回格式包含 draw_date (dd-mm-yyyy), max_id, 以及各类型号码数组。
    """
    valid_company(company)
    logging.info(f"收到全量数据请求: {company}")
    today = datetime.now().strftime("%Y-%m-%d")

    # 尝试获取当天数据
    rows = query_db(
        'SELECT id, type, number FROM results WHERE company = ? AND draw_date = ? ORDER BY id',
        [company, today]
    )
    if rows:
        target_date = today
        logging.info(f"使用当天日期: {target_date}")
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
        target_date = normalize_date(latest)  # 二次确保标准化
        logging.info(f"使用最新日期: {target_date}")
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

@app.route('/api/company/<company>/history', methods=['GET'])
def get_history(company):
    """
    历史数据接口：返回指定日期的数据。
    参数：date (必填)，格式 YYYY-MM-DD。
    返回格式：只包含号码分组（无 max_id），结构与全量接口一致。
    """
    valid_company(company)
    date_param = request.args.get('date')
    if not date_param:
        return jsonify({'error': 'Missing date parameter'}), 400
    if not DATE_RE.match(date_param):
        return jsonify({'error': 'Invalid date format'}), 400

    # 标准化日期（确保数据库查询格式一致）
    query_date = normalize_date(date_param)

    rows = query_db(
        'SELECT type, number FROM results WHERE company = ? AND draw_date = ? ORDER BY id',
        [company, query_date]
    )
    if not rows:
        logging.info(f"公司 {company} 在日期 {query_date} 无数据")
        return jsonify({})  # 返回空对象，前端会显示占位符

    result = {}
    for row in rows:
        t = row['type']
        num = row['number']
        result.setdefault(t, []).append(num)

    logging.info(f"返回 {company} 在 {query_date} 的历史数据")
    return jsonify(result)

@app.route('/api/company/<company>/latest', methods=['GET'])
def get_latest(company):
    """
    增量接口：返回当天自 after 之后新增的号码。
    参数：after (int)，可选，默认0。
    """
    valid_company(company)
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
    """健康检查，附带数据库文件存在状态"""
    db_exists = os.path.exists(DATABASE)
    return jsonify({'status': 'ok', 'database_exists': db_exists})

@app.route('/')
def index():
    """API 根路径，返回简单说明"""
    return jsonify({
        'name': '4D Results API',
        'endpoints': [
            '/api/health',
            '/api/company/<company>',
            '/api/company/<company>/history?date=YYYY-MM-DD',
            '/api/company/<company>/latest?after=<id>'
        ]
    })

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
    app.run(host='127.0.0.1', port=port, debug=False)
