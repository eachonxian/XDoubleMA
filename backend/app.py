from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import pandas as pd
from strategy_api import get_strategy_result, load_etf_codes

# 设置前端文件目录路径
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')

app = Flask(__name__, static_folder=frontend_dir)
CORS(app)  # 启用跨域请求支持

# 获取ETF代码列表
@app.route('/api/etf_codes', methods=['GET'])
def api_etf_codes():
    try:
        df = load_etf_codes()
        if df.empty:
            return jsonify({'success': False, 'message': '无法加载ETF代码列表'}), 404
        
        # 转换为JSON格式
        etf_list = []
        for _, row in df.iterrows():
            etf_list.append({
                'ts_code': row['ts_code'],
                'name': row['name']
            })
        
        return jsonify({
            'success': True,
            'data': etf_list
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取ETF代码出错: {str(e)}'}), 500

# 获取策略结果
@app.route('/api/strategy', methods=['POST'])
def api_strategy():
    try:
        data = request.json
        
        # 验证必要参数
        required_fields = ['ts_code', 'start_date', 'end_date', 'short_period', 'long_period']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'缺少必要参数: {field}'}), 400
        
        # 获取参数
        ts_code = data['ts_code']
        start_date = data['start_date']
        end_date = data['end_date']
        short_period = int(data['short_period'])
        long_period = int(data['long_period'])
        
        # 验证均线周期
        if short_period >= long_period:
            return jsonify({'success': False, 'message': '短周期均线必须小于长周期均线'}), 400
        
        # 获取策略结果
        result = get_strategy_result(ts_code, start_date, end_date, short_period, long_period)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': f'策略计算出错: {str(e)}'}), 500

# 提供前端静态文件访问
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_frontend(path):
    # 如果路径以 /api 开头，则不处理（由API路由处理）
    if path.startswith('api/'):
        return jsonify({'success': False, 'message': '无效的API路径'}), 404
    
    # 尝试提供请求的文件
    try:
        return send_from_directory(frontend_dir, path)
    except Exception as e:
        print(f"文件访问错误: {str(e)}")
        # 如果文件不存在，返回index.html（用于SPA应用）
        return send_from_directory(frontend_dir, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)