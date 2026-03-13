import os
import subprocess
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATABASE = '4d_results.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def query_db(query, args=(), one=False):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def get_latest_draw_date(company):
    """获取该公司最新有数据的日期（格式 YYYY-MM-DD），若无数据返回 None"""
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

    result = {
        'draw_date': datetime.strptime(target_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
        'max_id': 0
    }
    max_id = 0
    for row in rows:
        t = row['type']
        num = row['number']
        result.setdefault(t, []).append(num)  # 动态添加类型键
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
    data = [{'id': r['id'], 'type': r['type'], 'number': r['number']} for r in rows]
    return jsonify(data)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
