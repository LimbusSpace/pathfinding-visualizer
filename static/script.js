class PathfindingVisualizer {
    constructor() {
        this.grid = [];
        this.width = 20;
        this.height = 20;
        this.startPos = null;
        this.endPos = null;
        this.isDrawing = false;
        this.drawMode = 'wall';
        this.isAnimating = false;

        this.cellTypes = {
            EMPTY: 0,
            WALL: 1,
            START: 2,
            END: 3,
            PATH: 4,
            VISITED: 5,
            FRONTIER: 6
        };
    }

    initializeGrid(width, height) {
        this.width = width;
        this.height = height;
        this.grid = [];
        this.startPos = null;
        this.endPos = null;
        this.isAnimating = false;

        for (let y = 0; y < height; y++) {
            this.grid[y] = [];
            for (let x = 0; x < width; x++) {
                this.grid[y][x] = this.cellTypes.EMPTY;
            }
        }

        this.renderGrid();
        this.updateStatus('网格已初始化。右键设置起点，中键设置终点，左键绘制障碍物');
    }

    renderGrid() {
        const gridElement = document.getElementById('grid');
        gridElement.innerHTML = '';
        gridElement.style.gridTemplateColumns = `repeat(${this.width}, 1fr)`;

        for (let y = 0; y < this.height; y++) {
            for (let x = 0; x < this.width; x++) {
                const cell = document.createElement('div');
                cell.className = 'cell';
                cell.dataset.x = x;
                cell.dataset.y = y;

                this.updateCellAppearance(cell, this.grid[y][x]);

                // 鼠标事件
                cell.addEventListener('mousedown', (e) => this.onCellMouseDown(e, x, y));
                cell.addEventListener('mouseenter', (e) => this.onCellMouseEnter(x, y));
                cell.addEventListener('contextmenu', (e) => e.preventDefault());

                gridElement.appendChild(cell);
            }
        }

        // 全局鼠标事件
        document.addEventListener('mouseup', () => this.isDrawing = false);
        document.addEventListener('mouseleave', () => this.isDrawing = false);
    }

    updateCellAppearance(cell, cellType) {
        cell.className = 'cell';

        switch (cellType) {
            case this.cellTypes.EMPTY:
                cell.classList.add('empty');
                break;
            case this.cellTypes.WALL:
                cell.classList.add('wall');
                break;
            case this.cellTypes.START:
                cell.classList.add('start');
                break;
            case this.cellTypes.END:
                cell.classList.add('end');
                break;
            case this.cellTypes.PATH:
                cell.classList.add('path');
                break;
            case this.cellTypes.VISITED:
                cell.classList.add('visited');
                break;
            case this.cellTypes.FRONTIER:
                cell.classList.add('frontier');
                break;
        }
    }

    onCellMouseDown(e, x, y) {
        e.preventDefault();

        if (this.isAnimating) return;

        const cellType = this.grid[y][x];

        if (e.button === 0) { // 左键 - 绘制/擦除障碍物
            this.isDrawing = true;
            this.drawMode = cellType === this.cellTypes.WALL ? 'erase' : 'wall';
            this.setCellType(x, y, this.drawMode === 'wall' ? this.cellTypes.WALL : this.cellTypes.EMPTY);
        } else if (e.button === 2) { // 右键 - 设置起点
            if (this.startPos) {
                this.grid[this.startPos.y][this.startPos.x] = this.cellTypes.EMPTY;
            }
            this.startPos = {x, y};
            this.grid[y][x] = this.cellTypes.START;
            this.updateGridCell(x, y);
        } else if (e.button === 1) { // 中键 - 设置终点
            if (this.endPos) {
                this.grid[this.endPos.y][this.endPos.x] = this.cellTypes.EMPTY;
            }
            this.endPos = {x, y};
            this.grid[y][x] = this.cellTypes.END;
            this.updateGridCell(x, y);
            return false; // 防止中键滚动
        }
    }

    onCellMouseEnter(x, y) {
        if (this.isDrawing && !this.isAnimating) {
            this.setCellType(x, y, this.drawMode === 'wall' ? this.cellTypes.WALL : this.cellTypes.EMPTY);
        }
    }

    setCellType(x, y, type) {
        if (this.grid[y][x] === this.cellTypes.START || this.grid[y][x] === this.cellTypes.END) {
            return; // 不能覆盖起点和终点
        }
        this.grid[y][x] = type;
        this.updateGridCell(x, y);
    }

    updateGridCell(x, y) {
        const cell = document.querySelector(`[data-x="${x}"][data-y="${y}"]`);
        if (cell) {
            this.updateCellAppearance(cell, this.grid[y][x]);
        }
    }

    async startPathfinding() {
        if (this.isAnimating) return;

        if (!this.startPos || !this.endPos) {
            this.updateStatus('请先设置起点和终点');
            return;
        }

        this.isAnimating = true;
        document.getElementById('startBtn').disabled = true;
        this.updateStatus('正在寻路...');

        // 清除之前的路径显示
        this.clearPathDisplay();

        const algorithm = document.getElementById('algorithmSelect').value;
        const diagonal = document.getElementById('diagonalCheckbox').checked;
        const heuristic = document.getElementById('heuristicSelect').value;

        try {
            const response = await fetch('/set_grid', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ grid: this.grid })
            });

            if (!response.ok) {
                throw new Error('Failed to set grid');
            }

            const pathResponse = await fetch('/find_path', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    algorithm: algorithm,
                    diagonal: diagonal,
                    heuristic: heuristic
                })
            });

            if (!pathResponse.ok) {
                throw new Error('Failed to find path');
            }

            const result = await pathResponse.json();

            if (result.success) {
                await this.animatePathfinding(result.visited, result.path, result.found);

                if (result.found) {
                    this.updateStatus(`找到路径！路径长度：${result.path.length}，访问节点：${result.visited.length}`);
                } else {
                    this.updateStatus('未找到路径');
                }
            } else {
                this.updateStatus('寻路失败：' + result.error);
            }
        } catch (error) {
            this.updateStatus('错误：' + error.message);
        } finally {
            this.isAnimating = false;
            document.getElementById('startBtn').disabled = false;
        }
    }

    getAnimationSpeed() {
        const speed = document.getElementById('animationSpeed').value;
        switch (speed) {
            case 'fast':
                return { visited: 0, path: 20, batchSize: 15 }; // 最快基本无延迟
            case 'medium':
                return { visited: 3, path: 100, batchSize: 8 }; // 中等速度
            case 'slow':
                return { visited: 10, path: 200, batchSize: 3 }; // 最慢更详细
            default:
                return { visited: 0, path: 20, batchSize: 15 }; // 默认最快
        }
    }

    async animatePathfinding(visited, path, found) {
        const speed = this.getAnimationSpeed();
        const batchSize = speed.batchSize;

        // 动画显示访问过的节点
        for (let i = 0; i < visited.length; i++) {
            const [x, y] = visited[i];
            if (this.grid[y][x] === this.cellTypes.EMPTY) {
                this.grid[y][x] = this.cellTypes.VISITED;
                this.updateGridCell(x, y);
            }

            // 按批次暂停以控制速度
            if (i % batchSize === 0 && speed.visited > 0) {
                await new Promise(resolve => setTimeout(resolve, speed.visited));
            }
        }

        // 如果找到路径，动画显示路径
        if (found && path.length > 0) {
            await new Promise(resolve => setTimeout(resolve, 100)); // 短暂延迟

            for (let i = 0; i < path.length; i++) {
                const [x, y] = path[i];
                if (this.grid[y][x] !== this.cellTypes.START && this.grid[y][x] !== this.cellTypes.END) {
                    this.grid[y][x] = this.cellTypes.PATH;
                    this.updateGridCell(x, y);
                }
                if (speed.path > 0) {
                    await new Promise(resolve => setTimeout(resolve, speed.path));
                }
            }
        }
    }

    clearPathDisplay() {
        for (let y = 0; y < this.height; y++) {
            for (let x = 0; x < this.width; x++) {
                if (this.grid[y][x] === this.cellTypes.PATH || this.grid[y][x] === this.cellTypes.VISITED) {
                    this.grid[y][x] = this.cellTypes.EMPTY;
                    this.updateGridCell(x, y);
                }
            }
        }
    }

    async clearPath() {
        if (this.isAnimating) return;

        try {
            const response = await fetch('/clear_path', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                this.clearPathDisplay();
                this.updateStatus('路径已清除');
            }
        } catch (error) {
            this.updateStatus('清除路径失败：' + error.message);
        }
    }

    clearAll() {
        if (this.isAnimating) return;

        this.initializeGrid(this.width, this.height);
        this.updateStatus('网格已清空');
    }

    updateStatus(message) {
        document.getElementById('status').textContent = message;
    }
}

// 初始化应用
const visualizer = new PathfindingVisualizer();

// 更新网格输入框
function updateGridInputs() {
    const gridSize = document.getElementById('gridSize').value;
    const widthInput = document.getElementById('gridWidth');
    const heightInput = document.getElementById('gridHeight');

    switch (gridSize) {
        case 'small':
            widthInput.value = 20;
            heightInput.value = 20;
            break;
        case 'medium':
            widthInput.value = 30;
            heightInput.value = 30;
            break;
        case 'large':
            widthInput.value = 40;
            heightInput.value = 40;
            break;
    }
}

// 全局函数
async function initializeGrid() {
    const width = parseInt(document.getElementById('gridWidth').value);
    const height = parseInt(document.getElementById('gridHeight').value);

    visualizer.initializeGrid(width, height);

    try {
        const response = await fetch('/init_grid', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ width, height })
        });

        if (response.ok) {
            visualizer.updateStatus('网格初始化完成');
        } else {
            visualizer.updateStatus('网格初始化失败');
        }
    } catch (error) {
        visualizer.updateStatus('初始化失败：' + error.message);
    }
}

function startPathfinding() {
    visualizer.startPathfinding();
}

function clearPath() {
    visualizer.clearPath();
}

function clearAll() {
    visualizer.clearAll();
}

// LLM 相关功能
llmManager = {
    initialized: false,
    customAlgorithms: [],

    async init() {
        try {
            const response = await fetch('/llm/config');
            const config = await response.json();
            this.providers = config.providers;
            this.currentProvider = config.current_provider;
            this.initialized = true;
            this.updateAlgorithmList();
        } catch (error) {
            console.error('LLM 配置加载失败:', error);
        }
    },

    updateAlgorithmList() {
        const select = document.getElementById('customAlgorithmSelect');
        select.innerHTML = '<option value="">选择自定义算法</option>';

        this.customAlgorithms.forEach(algorithm => {
            const option = document.createElement('option');
            option.value = algorithm;
            option.textContent = algorithm;
            select.appendChild(option);
        });
    },

    async loadCustomAlgorithms() {
        try {
            const response = await fetch('/llm/custom_algorithms');
            const data = await response.json();
            if (data.success) {
                this.customAlgorithms = data.algorithms;
                this.updateAlgorithmList();
            }
        } catch (error) {
            console.error('加载自定义算法失败:', error);
        }
    }
};

// 页面加载时初始化
window.addEventListener('load', () => {
    initializeGrid();
    llmManager.init();
});

// LLM 设置相关的函数
function toggleLLMSettings() {
    const settings = document.getElementById('llmSettings');
    const btn = document.getElementById('llmSettingsBtn');

    if (settings.style.display === 'none') {
        settings.style.display = 'block';
        btn.textContent = '隐藏 LLM 设置';
    } else {
        settings.style.display = 'none';
        btn.textContent = '设置 LLM';
    }
}

function hideLLMSettings() {
    const settings = document.getElementById('llmSettings');
    const btn = document.getElementById('llmSettingsBtn');
    settings.style.display = 'none';
    btn.textContent = '设置 LLM';
}

async function saveApiKey() {
    const provider = document.getElementById('llmProvider').value;
    const apiKey = document.getElementById('apiKeyInput').value.trim();

    if (!apiKey) {
        alert('请输入API密钥');
        return;
    }

    try {
        const response = await fetch('/llm/set_api_key', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                provider: provider,
                api_key: apiKey
            })
        });

        const result = await response.json();
        if (result.success) {
            alert('API密钥保存成功');
            document.getElementById('apiKeyInput').value = '';
        } else {
            alert('保存失败: ' + result.error);
        }
    } catch (error) {
        alert('保存失败: ' + error.message);
    }
}

async function testConnection() {
    const provider = document.getElementById('llmProvider').value;
    const btn = document.getElementById('testConnectionBtn');

    btn.textContent = '测试中...';
    btn.disabled = true;

    try {
        const response = await fetch('/llm/test_connection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                provider: provider
            })
        });

        const result = await response.json();
        if (result.success) {
            if (result.connected) {
                alert('连接成功！API密钥可用');
            } else {
                alert('连接失败，请检查API密钥');
            }
        } else {
            alert('测试失败: ' + result.error);
        }
    } catch (error) {
        alert('测试失败: ' + error.message);
    } finally {
        btn.textContent = '测试连接';
        btn.disabled = false;
    }
}

async function generateAlgorithm() {
    const provider = document.getElementById('llmProvider').value;
    const description = document.getElementById('algorithmDescription').value.trim();
    const algorithmName = document.getElementById('algorithmName').value.trim();
    const generateBtn = document.getElementById('generateBtn');
    const codeArea = document.getElementById('generatedCode');

    if (!description) {
        alert('请输入算法描述');
        return;
    }

    if (!algorithmName) {
        alert('请输入算法名称');
        return;
    }

    generateBtn.textContent = '生成中...';
    generateBtn.disabled = true;
    codeArea.value = '正在生成算法代码...';

    try {
        const response = await fetch('/llm/generate_algorithm', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                provider: provider,
                description: description,
                name: algorithmName
            })
        });

        const result = await response.json();
        if (result.success) {
            codeArea.value = result.code;
            alert('算法生成成功！');
            llmManager.loadCustomAlgorithms();
        } else {
            codeArea.value = '生成失败: ' + result.error;
            alert('生成失败: ' + result.error);
        }
    } catch (error) {
        codeArea.value = '生成失败: ' + error.message;
        alert('生成失败: ' + error.message);
    } finally {
        generateBtn.textContent = '生成算法';
        generateBtn.disabled = false;
    }
}

async function executeCustomAlgorithm() {
    const algorithmSelect = document.getElementById('customAlgorithmSelect');
    const algorithmName = algorithmSelect.value;

    if (!algorithmName) {
        alert('请选择一个自定义算法');
        return;
    }

    if (!visualizer.startPos || !visualizer.endPos) {
        alert('请先设置起点和终点');
        return;
    }

    if (visualizer.isAnimating) {
        alert('正在执行寻路，请稍候');
        return;
    }

    visualizer.isAnimating = true;
    document.getElementById('startBtn').disabled = true;
    document.getElementById('executeCustomBtn').disabled = true;

    try {
        visualizer.updateStatus('正在执行自定义算法...');

        // 清除现有路径
        visualizer.clearPath();

        const response = await fetch('/llm/execute_custom', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: algorithmName
            })
        });

        const result = await response.json();
        if (result.success) {
            await visualizer.animateCustomPathfinding(result.path, result.visited, result.found);
        } else {
            visualizer.updateStatus('算法执行失败: ' + result.error);
        }
    } catch (error) {
        visualizer.updateStatus('执行失败: ' + error.message);
    } finally {
        visualizer.isAnimating = false;
        document.getElementById('startBtn').disabled = false;
        document.getElementById('executeCustomBtn').disabled = false;
    }
}

// 在 PathfindingVisualizer 类中添加自定义算法动画方法
PathfindingVisualizer.prototype.animateCustomPathfinding = async function(path, visited, found) {
    if (!visited || visited.length === 0) {
        this.updateStatus('没有访问任何节点');
        return;
    }

    const speed = this.getAnimationSpeed();
    let index = 0;

    // 动画显示访问的节点
    const animateVisited = () => {
        const batchSize = speed.batchSize;
        const endIndex = Math.min(index + batchSize, visited.length);

        for (let i = index; i < endIndex; i++) {
            const [y, x] = visited[i];
            if (this.grid[y][x] === this.cellTypes.EMPTY) {
                this.grid[y][x] = this.cellTypes.VISITED;
                this.updateCell(x, y);
            }
        }

        index = endIndex;

        if (index < visited.length) {
            setTimeout(animateVisited, speed.visited);
        } else {
            // 访问节点动画完成后，显示路径
            if (found && path && path.length > 0) {
                this.animateCustomPath(path, speed.path);
            } else {
                this.updateStatus('算法执行完成，未找到路径');
            }
        }
    };

    animateVisited();
};

PathfindingVisualizer.prototype.animateCustomPath = async function(path, delay) {
    let index = path.length - 1;

    const animatePath = () => {
        if (index >= 0) {
            const [y, x] = path[index];
            if (this.grid[y][x] === this.cellTypes.VISITED || this.grid[y][x] === this.cellTypes.EMPTY) {
                this.grid[y][x] = this.cellTypes.PATH;
                this.updateCell(x, y);
            }
            index--;
            setTimeout(animatePath, delay);
        } else {
            this.updateStatus('路径搜索完成');
        }
    };

    animatePath();
};