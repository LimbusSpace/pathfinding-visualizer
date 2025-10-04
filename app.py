from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from pathfinding import PathfindingAlgorithm, CellType
from llm_integration import llm_config, llm_generator, algorithm_executor, LLMProvider
import json
import webbrowser
import threading
import time

app = Flask(__name__)
CORS(app)

# 全局变量存储算法实例
algorithm_instance = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/init_grid', methods=['POST'])
def init_grid():
    global algorithm_instance
    data = request.json
    width = data.get('width', 20)
    height = data.get('height', 20)

    algorithm_instance = PathfindingAlgorithm(width, height)

    return jsonify({
        'success': True,
        'width': width,
        'height': height
    })

@app.route('/set_grid', methods=['POST'])
def set_grid():
    global algorithm_instance
    data = request.json
    grid_data = data.get('grid')

    if algorithm_instance and grid_data:
        algorithm_instance.set_grid(grid_data)
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Algorithm not initialized or grid data missing'}), 400

@app.route('/find_path', methods=['POST'])
def find_path():
    global algorithm_instance
    data = request.json
    algorithm_type = data.get('algorithm', 'astar')
    diagonal = data.get('diagonal', False)
    heuristic_method = data.get('heuristic', 'manhattan')

    if not algorithm_instance:
        return jsonify({'success': False, 'error': 'Algorithm not initialized'}), 400

    try:
        if algorithm_type == 'astar':
            result = algorithm_instance.astar(diagonal, heuristic_method)
        elif algorithm_type == 'dijkstra':
            result = algorithm_instance.dijkstra()
        elif algorithm_type == 'bfs':
            result = algorithm_instance.bfs()
        else:
            return jsonify({'success': False, 'error': 'Unknown algorithm'}), 400

        return jsonify({
            'success': True,
            'path': result['path'],
            'visited': result['visited'],
            'found': result['found']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/clear_path', methods=['POST'])
def clear_path():
    global algorithm_instance
    if algorithm_instance:
        # 重置路径和访问过的节点
        for y in range(algorithm_instance.height):
            for x in range(algorithm_instance.width):
                if algorithm_instance.grid[y][x] in [CellType.PATH, CellType.VISITED, CellType.FRONTIER]:
                    algorithm_instance.grid[y][x] = CellType.EMPTY
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Algorithm not initialized'}), 400

# LLM 相关路由
@app.route('/llm/config', methods=['GET'])
def get_llm_config():
    """获取LLM配置"""
    return jsonify({
        'providers': [
            {
                'id': provider.value,
                'name': provider.value,
                'configured': llm_config.is_provider_configured(provider)
            }
            for provider in LLMProvider
        ],
        'current_provider': llm_generator.current_provider.value
    })

@app.route('/llm/set_api_key', methods=['POST'])
def set_api_key():
    """设置API密钥"""
    data = request.json
    provider_name = data.get('provider')
    api_key = data.get('api_key')

    try:
        provider = LLMProvider(provider_name)
        llm_config.set_api_key(provider, api_key)
        return jsonify({'success': True})
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid provider'}), 400

@app.route('/llm/test_connection', methods=['POST'])
def test_connection():
    """测试API连接"""
    data = request.json
    provider_name = data.get('provider')

    try:
        provider = LLMProvider(provider_name)
        if not llm_config.is_provider_configured(provider):
            return jsonify({'success': False, 'error': 'API key not configured'})

        # 临时切换提供商进行测试
        original_provider = llm_generator.current_provider
        llm_generator.set_provider(provider)
        result = llm_generator.test_api_connection(provider)
        llm_generator.set_provider(original_provider)

        return jsonify({'success': True, 'connected': result})
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid provider'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/llm/generate_algorithm', methods=['POST'])
def generate_algorithm():
    """生成自定义算法"""
    data = request.json
    algorithm_description = data.get('description', '')
    provider_name = data.get('provider')
    algorithm_name = data.get('name', 'custom_algorithm')

    if not algorithm_description:
        return jsonify({'success': False, 'error': 'Algorithm description is required'}), 400

    try:
        provider = LLMProvider(provider_name)
        if not llm_config.is_provider_configured(provider):
            return jsonify({'success': False, 'error': 'API key not configured'})

        # 获取当前网格信息
        global algorithm_instance
        if not algorithm_instance:
            return jsonify({'success': False, 'error': 'Grid not initialized'}), 400

        # 生成算法
        original_provider = llm_generator.current_provider
        llm_generator.set_provider(provider)

        code = llm_generator.generate_custom_algorithm(
            algorithm_description,
            (algorithm_instance.width, algorithm_instance.height),
            algorithm_instance.start,
            algorithm_instance.end
        )

        llm_generator.set_provider(original_provider)

        if code:
            # 尝试加载算法
            if algorithm_executor.load_algorithm(algorithm_name, code):
                return jsonify({
                    'success': True,
                    'code': code,
                    'algorithm_name': algorithm_name
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Generated code is invalid or cannot be executed',
                    'code': code
                }), 400
        else:
            return jsonify({'success': False, 'error': 'Failed to generate algorithm'}), 500

    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid provider'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/llm/execute_custom', methods=['POST'])
def execute_custom_algorithm():
    """执行自定义算法"""
    global algorithm_instance
    data = request.json
    algorithm_name = data.get('name')

    if not algorithm_instance:
        return jsonify({'success': False, 'error': 'Algorithm not initialized'}), 400

    if algorithm_name not in algorithm_executor.custom_algorithms:
        return jsonify({'success': False, 'error': 'Custom algorithm not found'}), 400

    try:
        # 执行算法
        converted_grid = []
        for row in algorithm_instance.grid:
            converted_row = []
            for cell in row:
                converted_row.append(cell.value)
            converted_grid.append(converted_row)

        path, visited_order = algorithm_executor.execute_algorithm(
            algorithm_name,
            algorithm_instance.width,
            algorithm_instance.height,
            converted_grid,
            algorithm_instance.start,
            algorithm_instance.end
        )

        return jsonify({
            'success': True,
            'path': path,
            'visited': visited_order,
            'found': len(path) > 0
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/llm/custom_algorithms', methods=['GET'])
def get_custom_algorithms():
    """获取自定义算法列表"""
    return jsonify({
        'success': True,
        'algorithms': algorithm_executor.get_available_algorithms()
    })

@app.route('/llm/remove_algorithm', methods=['POST'])
def remove_algorithm():
    """移除自定义算法"""
    data = request.json
    algorithm_name = data.get('name')

    if algorithm_executor.remove_algorithm(algorithm_name):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Algorithm not found'}), 400

def open_browser():
    """延迟打开浏览器，确保服务器已启动"""
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    # 启动浏览器线程
    threading.Thread(target=open_browser, daemon=True).start()
    # 启动Flask服务器
    app.run(debug=True, host='0.0.0.0', port=5000)