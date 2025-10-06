from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from pathfinding import PathfindingAlgorithm, CellType
from llm_integration import llm_config, llm_generator, algorithm_executor, LLMProvider
from code_validator import CodeValidator
from llm_code_fixer import LLMCodeFixer, FixProgress
from progress_manager import progress_manager, TaskType, TaskStatus
import json
import webbrowser
import threading
import time
import uuid

app = Flask(__name__)
CORS(app)

# 全局变量存储算法实例
algorithm_instance = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/algorithm_library')
def algorithm_library():
    return render_template('algorithm_library.html')

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
        print(f"🔍 [DEBUG] 执行自定义算法请求: algorithm_name={algorithm_name}")
        print(f"🔍 [DEBUG] 可用的算法列表: {list(algorithm_executor.custom_algorithms.keys())}")

        if not algorithm_instance:
            print("🔍 [ERROR] algorithm_instance 未初始化")
            return jsonify({'success': False, 'error': 'Algorithm not initialized'}), 400

        if algorithm_name not in algorithm_executor.custom_algorithms:
            print(f"🔍 [ERROR] 算法 {algorithm_name} 不在 available_algorithms 中")
            return jsonify({'success': False, 'error': 'Custom algorithm not found'}), 400

        print(f"🔍 [DEBUG] 开始执行算法 {algorithm_name}")
        print(f"🔍 [DEBUG] 网格大小: {algorithm_instance.width}x{algorithm_instance.height}")
        print(f"🔍 [DEBUG] 起点: {algorithm_instance.start}, 终点: {algorithm_instance.end}")

        # 执行算法 - 直接传递CellType值，让算法执行器处理转换
        raw_grid = []
        for row in algorithm_instance.grid:
            raw_row = []
            for cell in row:
                raw_row.append(cell.value)
            raw_grid.append(raw_row)

        path, visited_order = algorithm_executor.execute_algorithm(
            algorithm_name,
            algorithm_instance.width,
            algorithm_instance.height,
            raw_grid,
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
    """移除自定义算法 (旧接口，保持兼容)"""
    data = request.json
    algorithm_name = data.get('name')

    if algorithm_executor.remove_algorithm(algorithm_name):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Algorithm not found'}), 400

@app.route('/llm/delete_algorithm', methods=['POST'])
def delete_algorithm():
    """删除自定义算法"""
    data = request.json
    algorithm_name = data.get('name')

    if algorithm_executor.remove_algorithm(algorithm_name):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Algorithm not found'}), 400

@app.route('/llm/get_algorithm', methods=['POST'])
def get_algorithm():
    """获取算法代码"""
    data = request.json
    algorithm_name = data.get('name')

    if algorithm_name in algorithm_executor.custom_algorithms:
        return jsonify({
            'success': True,
            'code': algorithm_executor.custom_algorithms[algorithm_name]['code']
        })
    else:
        return jsonify({'success': False, 'error': 'Algorithm not found'}), 400

@app.route('/llm/get_algorithm_info', methods=['POST'])
def get_algorithm_info():
    """获取算法信息"""
    data = request.json
    algorithm_name = data.get('name')

    if algorithm_name in algorithm_executor.custom_algorithms:
        algorithm_info = algorithm_executor.custom_algorithms[algorithm_name]
        return jsonify({
            'success': True,
            'description': algorithm_info.get('description', ''),
            'created_at': algorithm_info.get('created_at', '')
        })
    else:
        return jsonify({'success': False, 'error': 'Algorithm not found'}), 400

@app.route('/llm/save_algorithm', methods=['POST'])
def save_algorithm():
    """保存算法"""
    data = request.json
    algorithm_name = data.get('name')
    description = data.get('description', '')
    code = data.get('code')
    old_name = data.get('old_name')  # 如果是重命名，提供旧名称

    if not algorithm_name or not code:
        return jsonify({'success': False, 'error': 'Algorithm name and code are required'}), 400

    try:
        # 如果是重命名，先删除旧的
        if old_name and old_name != algorithm_name and old_name in algorithm_executor.custom_algorithms:
            algorithm_executor.remove_algorithm(old_name)

        # 尝试加载新算法以验证代码
        if algorithm_executor.load_algorithm(algorithm_name, code, description):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Algorithm code is invalid or cannot be loaded'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 代码验证和修复相关的路由
@app.route('/llm/validate_code', methods=['POST'])
def validate_code():
    """验证算法代码"""
    data = request.json
    code = data.get('code', '')
    algorithm_name = data.get('algorithm_name', 'CustomPathfindingAlgorithm')

    if not code:
        return jsonify({'success': False, 'error': 'Code is required'}), 400

    try:
        validator = CodeValidator()
        result = validator.validate_algorithm_code(code, algorithm_name)

        return jsonify({
            'success': True,
            'validation_result': {
                'is_valid': result.is_valid,
                'overall_score': result.overall_score,
                'errors': [
                    {
                        'level': error.level.value,
                        'message': error.message,
                        'line_number': error.line_number,
                        'suggestion': error.suggestion,
                        'code_snippet': error.code_snippet
                    }
                    for error in result.errors
                ],
                'warnings': [
                    {
                        'level': warning.level.value,
                        'message': warning.message,
                        'line_number': warning.line_number,
                        'suggestion': warning.suggestion,
                        'code_snippet': warning.code_snippet
                    }
                    for warning in result.warnings
                ],
                'suggestions': [
                    {
                        'level': suggestion.level.value,
                        'message': suggestion.message,
                        'line_number': suggestion.line_number,
                        'suggestion': suggestion.suggestion,
                        'code_snippet': suggestion.code_snippet
                    }
                    for suggestion in result.suggestions
                ]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/llm/fix_code', methods=['POST'])
def fix_code():
    """启动代码修复任务"""
    data = request.json
    code = data.get('code', '')
    algorithm_name = data.get('algorithm_name', 'CustomPathfindingAlgorithm')

    if not code:
        return jsonify({'success': False, 'error': 'Code is required'}), 400

    try:
        # 创建任务ID
        task_id = f"fix_{uuid.uuid4().hex}"

        # 创建任务
        task = progress_manager.create_task(
            task_id=task_id,
            task_type=TaskType.FIXING,
            title="🔧 算法代码修复",
            description=f"修复 {algorithm_name} 算法的代码错误",
            total_steps=5
        )

        # 启动后台修复任务
        def run_fix_task():
            try:
                # 开始任务
                progress_manager.start_task(task_id)
                progress_manager.update_step(task_id, 1, "初始化LLM代码修复器...")

                # 创建LLM修复器
                fixer = LLMCodeFixer(llm_config)
                if data.get('provider'):
                    provider = LLMProvider(data.get('provider'))
                    fixer.set_provider(provider)

                progress_manager.update_step(task_id, 2, "开始分析代码错误...")

                # 定义进度回调
                def progress_callback(progress_data):
                    if 'current_step_name' in progress_data:
                        step_name = progress_data['current_step_name']
                        progress = progress_data.get('overall_progress', 0)
                        progress_manager.update_progress(task_id, progress, step_name)

                progress_manager.update_step(task_id, 3, "进行代码修复...")

                # 执行修复
                fix_result = fixer.fix_algorithm_code(
                    code,
                    algorithm_name,
                    progress_callback=progress_callback
                )

                progress_manager.update_step(task_id, 4, "验证修复结果...")

                if fix_result['success']:
                    progress_manager.update_progress(task_id, 95, "修复完成")
                    progress_manager.update_step(task_id, 5, "✅ 代码修复成功")
                    progress_manager.complete_task(task_id, fix_result)
                else:
                    progress_manager.fail_task(task_id, f"修复失败: {fix_result.get('error', 'Unknown error')}")

            except Exception as e:
                progress_manager.fail_task(task_id, f"任务执行失败: {str(e)}")

        # 在后台线程中运行
        threading.Thread(target=run_fix_task, daemon=True).start()

        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '代码修复任务已启动'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/llm/generate_and_fix_algorithm', methods=['POST'])
def generate_and_fix_algorithm():
    """生成并自动修复算法代码"""
    data = request.json
    algorithm_description = data.get('description', '')
    provider_name = data.get('provider')
    algorithm_name = data.get('name', 'custom_algorithm')

    if not algorithm_description:
        return jsonify({'success': False, 'error': 'Algorithm description is required'}), 400

    try:
        # 创建任务ID
        task_id = f"generate_fix_{uuid.uuid4().hex}"

        # 创建任务
        task = progress_manager.create_task(
            task_id=task_id,
            task_type=TaskType.GENERATION,
            title="🤖 生成并修复算法",
            description=f"生成 {algorithm_name} 算法并自动修复错误",
            total_steps=7
        )

        # 启动后台修复任务
        def run_generation_and_fix_task():
            try:
                # 开始任务
                progress_manager.start_task(task_id)
                progress_manager.update_step(task_id, 1, "初始化生成器...")

                # 设置LLM提供商
                provider = LLMProvider(provider_name)
                if not llm_config.is_provider_configured(provider):
                    progress_manager.fail_task(task_id, "API key not configured")
                    return

                # 获取当前网格信息
                global algorithm_instance
                if not algorithm_instance:
                    progress_manager.fail_task(task_id, "Grid not initialized")
                    return

                # 设置LLM生成器
                original_provider = llm_generator.current_provider
                llm_generator.set_provider(provider)

                progress_manager.update_step(task_id, 2, "生成算法代码...")

                # 生成算法
                code = llm_generator.generate_custom_algorithm(
                    algorithm_description,
                    (algorithm_instance.width, algorithm_instance.height),
                    algorithm_instance.start,
                    algorithm_instance.end
                )

                llm_generator.set_provider(original_provider)

                if not code:
                    progress_manager.fail_task(task_id, "Failed to generate algorithm")
                    return

                progress_manager.update_step(task_id, 3, "验证生成的代码...")

                # 验证生成的代码
                validator = CodeValidator()
                initial_result = validator.validate_algorithm_code(code, algorithm_name)

                if initial_result.is_valid:
                    progress_manager.update_step(task_id, 7, "✅ 代码生成完成且验证通过")
                    progress_manager.complete_task(task_id, {
                        'code': code,
                        'validation_result': initial_result,
                        'generations': 1,
                        'fixes': 0
                    })
                    return

                progress_manager.update_step(task_id, 4, "发现错误，启动自动修复...")

                # 创建LLM修复器
                fixer = LLMCodeFixer(llm_config)
                fixer.set_provider(provider)

                progress_manager.update_step(task_id, 5, "进行代码修复...")

                # 定义进度回调
                def progress_callback(progress_data):
                    if 'current_step_name' in progress_data:
                        step_name = progress_data['current_step_name']
                        progress = (progress_data.get('overall_progress', 0) * 30 / 100) + 60  # 60-90% 范围
                        progress_manager.update_progress(task_id, progress, step_name)

                # 执行修复
                fix_result = fixer.fix_algorithm_code(
                    code,
                    algorithm_name,
                    progress_callback=progress_callback
                )

                progress_manager.update_step(task_id, 6, "验证最终结果...")

                if fix_result['success']:
                    progress_manager.update_progress(task_id, 95, "生成和修复完成")
                    final_validator = CodeValidator()
                    final_result = final_validator.validate_algorithm_code(fix_result['final_code'], algorithm_name)

                    # 尝试加载算法
                    if algorithm_executor.load_algorithm(algorithm_name, fix_result['final_code']):
                        progress_manager.update_step(task_id, 7, "✅ 算法生成并修复成功")
                        progress_manager.complete_task(task_id, {
                            'code': fix_result['final_code'],
                            'validation_result': final_result,
                            'generations': 1,
                            'fixes': fix_result['iterations'],
                            'fix_history': fix_result.get('fix_history', [])
                        })
                    else:
                        progress_manager.fail_task(task_id, "代码修复成功但无法加载到执行器")
                else:
                    progress_manager.fail_task(task_id, f"修复失败: {fix_result.get('error', 'Unknown error')}")

            except Exception as e:
                progress_manager.fail_task(task_id, f"任务执行失败: {str(e)}")

        # 在后台线程中运行
        threading.Thread(target=run_generation_and_fix_task, daemon=True).start()

        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '算法生成和修复任务已启动'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 任务管理路由
@app.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """获取任务状态"""
    task = progress_manager.get_task(task_id)
    if task:
        return jsonify({
            'success': True,
            'task': task.to_dict()
        })
    else:
        return jsonify({'success': False, 'error': 'Task not found'}), 404

@app.route('/tasks', methods=['GET'])
def get_all_tasks():
    """获取所有任务"""
    tasks = progress_manager.get_all_tasks()
    return jsonify({
        'success': True,
        'tasks': [task.to_dict() for task in tasks]
    })

@app.route('/tasks/<task_id>/pause', methods=['POST'])
def pause_task(task_id):
    """暂停任务"""
    if progress_manager.pause_task(task_id):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to pause task'}), 400

@app.route('/tasks/<task_id>/resume', methods=['POST'])
def resume_task(task_id):
    """恢复任务"""
    if progress_manager.resume_task(task_id):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to resume task'}), 400

@app.route('/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """取消任务"""
    if progress_manager.cancel_task(task_id):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to cancel task'}), 400

@app.route('/tasks/<task_id>/remove', methods=['DELETE'])
def remove_task(task_id):
    """移除任务"""
    if progress_manager.remove_task(task_id):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to remove task'}), 400

def open_browser():
    """延迟打开浏览器，确保服务器已启动"""
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    # 启动浏览器线程
    threading.Thread(target=open_browser, daemon=True).start()
    # 启动Flask服务器
    app.run(debug=True, host='0.0.0.0', port=5000)