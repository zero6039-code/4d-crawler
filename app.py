from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)  # 允许跨域请求，方便前端本地调试

DATABASE = '4d_results.db'

def get_db_connection():
    """获取数据库连接，并设置 row_factory 为字典模式"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def query_db(query, args=(), one=False):
    """执行查询并返回结果（自动处理连接关闭）"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/api/company/<company>', methods=['GET'])
def get_full_data(company):
    """
    全量接口：返回该公司所有已开号码（按类型分组）
    同时返回当前最大 ID，便于前端初始化轮询起始点
    """
    rows = query_db(
        'SELECT id, type, number FROM results WHERE company = ? ORDER BY id',
        [company]
    )
    # 初始化返回结构
    result = {
        'special': [],
        'consolation': [],
        'prize': [],
        'max_id': 0
    }
    max_id = 0
    for row in rows:
        t = row['type']
        number = row['number']
        # 将号码添加到对应类型数组中
        if t in result:
            result[t].append(number)
        else:
            # 如果遇到未预定义的类型（如 'prize1'），可以创建新数组，或统一归入其他
            result.setdefault(t, []).append(number)
        # 更新最大 ID
        if row['id'] > max_id:
            max_id = row['id']
    result['max_id'] = max_id
    return jsonify(result)

@app.route('/api/company/<company>/latest', methods=['GET'])
def get_latest(company):
    """
    增量接口：返回自 after 之后新增的号码
    参数：after (int) - 上次接收到的最大 ID
    返回：数组，每个元素包含 id, type, number
    """
    after = request.args.get('after', 0, type=int)
    rows = query_db(
        'SELECT id, type, number FROM results WHERE company = ? AND id > ? ORDER BY id',
        [company, after]
    )
    data = [{'id': r['id'], 'type': r['type'], 'number': r['number']} for r in rows]
    return jsonify(data)

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查，可选"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)