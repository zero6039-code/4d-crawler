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

DATABASE = '4d_results.db'
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
    return jsonify({'status': 'ok'})

@app.route('/api/trigger-crawler', methods=['GET'])
def trigger_crawler():
    secret = request.args.get('secret')
    if secret != CRAWLER_SECRET:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        result = subprocess.run([sys.executable, 'crawler.py'],
                                capture_output=True, text=True, timeout=300)
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
