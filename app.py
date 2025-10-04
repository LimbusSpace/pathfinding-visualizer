from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from pathfinding import PathfindingAlgorithm, CellType
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

def open_browser():
    """延迟打开浏览器，确保服务器已启动"""
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    # 启动浏览器线程
    threading.Thread(target=open_browser, daemon=True).start()
    # 启动Flask服务器
    app.run(debug=True, host='0.0.0.0', port=5000)