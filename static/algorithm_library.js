// 算法库管理功能
class AlgorithmLibrary {
    constructor() {
        this.algorithms = [];
        this.currentEditingAlgorithm = null;
        this.init();
    }

    init() {
        this.loadAlgorithms();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // 编辑表单提交
        document.getElementById('editForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveAlgorithm();
        });
    }

    async loadAlgorithms() {
        try {
            const response = await fetch('/llm/custom_algorithms');
            const data = await response.json();

            if (data.success) {
                this.algorithms = data.algorithms;
                this.renderAlgorithmList();
            } else {
                this.showStatus('加载算法列表失败: ' + data.error, 'error');
            }
        } catch (error) {
            this.showStatus('网络错误: ' + error.message, 'error');
        }
    }

    renderAlgorithmList() {
        const container = document.getElementById('algorithmList');

        if (this.algorithms.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>📂 暂无自定义算法</h3>
                    <p>点击"创建新算法"开始编写您的第一个寻路算法</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.algorithms.map(algorithm => `
            <div class="algorithm-card">
                <div class="algorithm-header">
                    <div class="algorithm-info">
                        <h3>${this.escapeHtml(algorithm.name)}</h3>
                        <p>创建时间: ${new Date(algorithm.created_at).toLocaleString()}</p>
                        ${algorithm.description ? `<p>描述: ${this.escapeHtml(algorithm.description)}</p>` : ''}
                    </div>
                    <div class="algorithm-actions">
                        <button class="btn btn-primary" onclick="algorithmLibrary.viewAlgorithm('${this.escapeHtml(algorithm.name)}')">👁️ 查看</button>
                        <button class="btn btn-secondary" onclick="algorithmLibrary.editAlgorithm('${this.escapeHtml(algorithm.name)}')">✏️ 编辑</button>
                        <button class="btn btn-danger" onclick="algorithmLibrary.deleteAlgorithm('${this.escapeHtml(algorithm.name)}')">🗑️ 删除</button>
                    </div>
                </div>
                <div id="preview-${this.escapeHtml(algorithm.name).replace(/\s+/g, '-')}" class="code-preview" style="display: none;"></div>
            </div>
        `).join('');
    }

    async viewAlgorithm(name) {
        const previewId = 'preview-' + name.replace(/\s+/g, '-');
        const previewElement = document.getElementById(previewId);

        if (previewElement.style.display === 'none') {
            try {
                const response = await fetch('/llm/get_algorithm', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name: name })
                });

                const result = await response.json();
                if (result.success) {
                    previewElement.textContent = result.code;
                    previewElement.style.display = 'block';
                } else {
                    this.showStatus('获取算法代码失败: ' + result.error, 'error');
                }
            } catch (error) {
                this.showStatus('网络错误: ' + error.message, 'error');
            }
        } else {
            previewElement.style.display = 'none';
        }
    }

    async editAlgorithm(name) {
        try {
            const response = await fetch('/llm/get_algorithm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name: name })
            });

            const result = await response.json();
            if (result.success) {
                this.currentEditingAlgorithm = name;
                document.getElementById('modalTitle').textContent = '编辑算法 - ' + name;
                document.getElementById('algorithmName').value = name;
                document.getElementById('algorithmCode').value = result.code;

                // 获取算法描述
                const descResponse = await fetch('/llm/get_algorithm_info', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name: name })
                });

                const descResult = await descResponse.json();
                if (descResult.success) {
                    document.getElementById('algorithmDescription').value = descResult.description || '';
                } else {
                    document.getElementById('algorithmDescription').value = '';
                }

                document.getElementById('editModal').style.display = 'block';
            } else {
                this.showStatus('获取算法代码失败: ' + result.error, 'error');
            }
        } catch (error) {
            this.showStatus('网络错误: ' + error.message, 'error');
        }
    }

    async deleteAlgorithm(name) {
        if (!confirm(`确定要删除算法 "${name}" 吗？此操作不可恢复。`)) {
            return;
        }

        try {
            const response = await fetch('/llm/delete_algorithm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name: name })
            });

            const result = await response.json();
            if (result.success) {
                this.showStatus('算法删除成功', 'success');
                this.loadAlgorithms(); // 重新加载列表
            } else {
                this.showStatus('删除算法失败: ' + result.error, 'error');
            }
        } catch (error) {
            this.showStatus('网络错误: ' + error.message, 'error');
        }
    }

    createNewAlgorithm() {
        this.currentEditingAlgorithm = null;
        document.getElementById('modalTitle').textContent = '创建新算法';
        document.getElementById('algorithmName').value = '';
        document.getElementById('algorithmDescription').value = '';
        document.getElementById('algorithmCode').value = `from typing import List, Tuple, Optional
from enum import Enum
from collections import deque

class CustomPathfindingAlgorithm:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.visited_order = []

    def find_path(self, grid, start, end) -> List[Tuple[int, int]]:
        """
        主要寻路方法 - BFS算法示例

        参数:
            grid: 二维数组，0=空地, 1=障碍物, 2=起点, 3=终点
            start: 起点坐标 (y, x)
            end: 终点坐标 (y, x)

        返回:
            路径坐标列表 [(y1, x1), (y2, x2), ...]
        """
        if start == end:
            return [start]

        def is_valid(pos):
            y, x = pos
            return (0 <= y < self.height and
                    0 <= x < self.width and
                    grid[y][x] != 1)  # 1 表示障碍物

        def get_neighbors(pos):
            y, x = pos
            neighbors = []
            # 四个方向：上、下、左、右
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

            for dy, dx in directions:
                new_pos = (y + dy, x + dx)
                if is_valid(new_pos):
                    neighbors.append(new_pos)
            return neighbors

        # BFS算法实现
        queue = deque([start])
        visited = set([start])
        parent = {start: None}

        # 记录访问顺序用于可视化
        self.visited_order = [start]

        while queue:
            current = queue.popleft()

            if current == end:
                # 重建路径
                path = []
                while current is not None:
                    path.append(current)
                    current = parent[current]
                path.reverse()
                return path

            for neighbor in get_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)
                    self.visited_order.append(neighbor)

        return []  # 未找到路径

    def get_visited_order(self) -> List[Tuple[int, int]]:
        """
        获取访问节点的顺序（用于可视化）

        返回:
            访问顺序列表 [(y1, x1), (y2, x2), ...]
        """
        return self.visited_order`;
        document.getElementById('editModal').style.display = 'block';
    }

    async saveAlgorithm() {
        const name = document.getElementById('algorithmName').value.trim();
        const description = document.getElementById('algorithmDescription').value.trim();
        const code = document.getElementById('algorithmCode').value.trim();

        if (!name) {
            alert('请输入算法名称');
            return;
        }

        if (!code) {
            alert('请输入算法代码');
            return;
        }

        try {
            const response = await fetch('/llm/save_algorithm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: name,
                    description: description,
                    code: code,
                    old_name: this.currentEditingAlgorithm // 如果是编辑，提供旧名称
                })
            });

            const result = await response.json();
            if (result.success) {
                this.showStatus(
                    this.currentEditingAlgorithm ? '算法更新成功' : '算法创建成功',
                    'success'
                );
                this.closeEditModal();
                this.loadAlgorithms(); // 重新加载列表
            } else {
                this.showStatus('保存算法失败: ' + result.error, 'error');
            }
        } catch (error) {
            this.showStatus('网络错误: ' + error.message, 'error');
        }
    }

    closeEditModal() {
        document.getElementById('editModal').style.display = 'none';
        this.currentEditingAlgorithm = null;
    }

    viewExamples() {
        document.getElementById('examplesModal').style.display = 'block';
    }

    closeExamplesModal() {
        document.getElementById('examplesModal').style.display = 'none';
    }

    refreshAlgorithmList() {
        this.loadAlgorithms();
    }

    showStatus(message, type) {
        const statusElement = document.getElementById('statusMessage');
        statusElement.textContent = message;
        statusElement.className = `status-message status-${type}`;
        statusElement.style.display = 'block';

        // 3秒后自动隐藏
        setTimeout(() => {
            statusElement.style.display = 'none';
        }, 3000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 全局函数
let algorithmLibrary;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    algorithmLibrary = new AlgorithmLibrary();
});

// 全局函数供HTML调用
function createNewAlgorithm() {
    algorithmLibrary.createNewAlgorithm();
}

function refreshAlgorithmList() {
    algorithmLibrary.refreshAlgorithmList();
}

function viewExamples() {
    algorithmLibrary.viewExamples();
}

function closeEditModal() {
    algorithmLibrary.closeEditModal();
}

function closeExamplesModal() {
    algorithmLibrary.closeExamplesModal();
}