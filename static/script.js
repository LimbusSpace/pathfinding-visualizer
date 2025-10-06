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

            let result;

            // 检查是否为自定义算法
            if (llmManager.isCustomAlgorithm(algorithm)) {
                const customAlgorithmName = llmManager.getCustomAlgorithmName(algorithm);
                console.log('🔍 执行自定义算法:', algorithm, '算法名称:', customAlgorithmName);

                const customResponse = await fetch('/llm/execute_custom', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        name: customAlgorithmName
                    })
                });

                console.log('🔍 自定义算法响应状态:', customResponse.status);

                if (!customResponse.ok) {
                    const errorData = await customResponse.json();
                    console.error('🔍 自定义算法执行失败:', errorData);
                    throw new Error('Failed to execute custom algorithm: ' + errorData.error);
                }

                result = await customResponse.json();
                console.log('🔍 自定义算法执行结果:', result);
            } else {
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

                result = await pathResponse.json();
            }

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
        const visitedSpeed = document.getElementById('visitedSpeed').value;
        const movementSpeed = document.getElementById('movementSpeed').value;

        let visitedDelay, pathDelay, batchSize;

        // 设置已访问路径速度（比原来慢两个档次）
        switch (visitedSpeed) {
            case 'fast':
                visitedDelay = 10;      // 原来是 0，现在是 10
                batchSize = 15;
                break;
            case 'medium':
                visitedDelay = 30;     // 原来是 3，现在是 30
                batchSize = 8;
                break;
            case 'slow':
                visitedDelay = 100;    // 原来是 10，现在是 100
                batchSize = 3;
                break;
            case 'very-slow':
                visitedDelay = 200;    // 新增的很慢档位
                batchSize = 2;
                break;
            case 'ultra-slow':
                visitedDelay = 400;    // 新增的极慢档位
                batchSize = 1;
                break;
            default:
                visitedDelay = 10;
                batchSize = 15;
        }

        // 设置移动路径速度（保持原来的速度）
        switch (movementSpeed) {
            case 'fast':
                pathDelay = 20;
                break;
            case 'medium':
                pathDelay = 100;
                break;
            case 'slow':
                pathDelay = 200;
                break;
            default:
                pathDelay = 20;
        }

        return { visited: visitedDelay, path: pathDelay, batchSize: batchSize };
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
    currentTaskId: null,
    taskRefreshInterval: null,

    async init() {
        try {
            const response = await fetch('/llm/config');
            const config = await response.json();
            this.providers = config.providers;
            this.currentProvider = config.current_provider;
            this.initialized = true;
            this.loadCustomAlgorithms();
            this.startTaskMonitoring();
        } catch (error) {
            console.error('LLM 配置加载失败:', error);
        }
    },

    updateAlgorithmList() {
        const customGroup = document.getElementById('customAlgorithmsGroup');
        if (!customGroup) return;

        // 清除现有的自定义算法选项
        customGroup.innerHTML = '';

        this.customAlgorithms.forEach(algorithm => {
            const option = document.createElement('option');
            // 使用算法的name字段作为值，description作为显示文本
            option.value = 'custom_' + algorithm.name;
            // 🔧 修复：使用description字段而不是整个对象
            option.textContent = algorithm.description || algorithm.name;
            customGroup.appendChild(option);
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
    },

    isCustomAlgorithm(algorithm) {
        return algorithm.startsWith('custom_');
    },

    getCustomAlgorithmName(algorithm) {
        // 🔧 修复：现在algorithm格式是 'custom_algorithmName'，需要移除前缀
        return algorithm.startsWith('custom_') ? algorithm.substring(7) : algorithm;
    },

    startTaskMonitoring() {
        // 启动任务监控
        this.taskRefreshInterval = setInterval(() => {
            if (this.currentTaskId) {
                this.pollTaskStatus(this.currentTaskId);
            }
        }, 1000);
    },

    stopTaskMonitoring() {
        if (this.taskRefreshInterval) {
            clearInterval(this.taskRefreshInterval);
            this.taskRefreshInterval = null;
        }
    },

    async pollTaskStatus(taskId) {
        try {
            const response = await fetch(`/tasks/${taskId}`);
            const result = await response.json();

            if (result.success) {
                const task = result.task;
                this.updateTaskDisplay(task);

                // 如果任务完成或失败，停止轮询
                if (task.status === 'completed' || task.status === 'failed' || task.status === 'cancelled') {
                    this.currentTaskId = null;
                    if (task.status === 'completed') {
                        showSuccessMessage('任务完成！');
                        // 如果是生成任务，自动填充生成的代码
                        if (task.result && task.result.code) {
                            document.getElementById('generatedCode').value = task.result.code;
                            this.loadCustomAlgorithms(); // 刷新算法列表
                        }
                    }
                }
            }
        } catch (error) {
            console.error('获取任务状态失败:', error);
        }
    },

    updateTaskDisplay(task) {
        const container = document.getElementById('tasksContainer');
        if (!container) return;

        const taskElement = document.getElementById(`task-${task.task_id}`);
        if (taskElement) {
            // 更新现有任务元素
            taskElement.innerHTML = this.renderTaskHTML(task);
        } else {
            // 添加新任务元素
            const taskDiv = document.createElement('div');
            taskDiv.id = `task-${task.task_id}`;
            taskDiv.className = 'task-card';
            taskDiv.innerHTML = this.renderTaskHTML(task);
            container.insertBefore(taskDiv, container.firstChild);
        }
    },

    renderTaskHTML(task) {
        const statusColors = {
            pending: 'bg-gray-500',
            running: 'bg-blue-500',
            paused: 'bg-yellow-500',
            completed: 'bg-green-500',
            failed: 'bg-red-500',
            cancelled: 'bg-gray-400'
        };

        const statusIcons = {
            pending: '⏳',
            running: '🔄',
            paused: '⏸️',
            completed: '✅',
            failed: '❌',
            cancelled: '🚫'
        };

        const colorClass = statusColors[task.status] || 'bg-gray-500';
        const icon = statusIcons[task.status] || '❓';

        const elapsed = task.elapsed_time.toFixed(1);
        const remaining = task.estimated_remaining_time ? task.estimated_remaining_time.toFixed(1) : null;

        const timeStr = elapsed + 's';
        if (remaining) {
            timeStr += ` / 剩余 ${remaining}s`;
        }

        let actionsHtml = '';
        if (task.status === 'running') {
            actionsHtml = `<button onclick="pauseTask('${task.task_id}')" class="btn-small">⏸️</button>`;
        } else if (task.status === 'paused') {
            actionsHtml = `<button onclick="resumeTask('${task.task_id}')" class="btn-small">▶️</button>`;
        }
        if (task.status === 'running' || task.status === 'paused') {
            actionsHtml += `<button onclick="cancelTask('${task.task_id}')" class="btn-small">🚫</button>`;
        }
        actionsHtml += `<button onclick="removeTask('${task.task_id}')" class="btn-small">🗑️</button>`;

        return `
            <div class="task-header">
                <div class="task-info">
                    <span class="task-icon">${icon}</span>
                    <span class="task-title">${task.title}</span>
                </div>
                <div class="task-time">${timeStr}</div>
            </div>
            <div class="task-description">${task.description}</div>
            <div class="task-status-bar">
                <div class="progress-bar">
                    <div class="progress-fill ${colorClass}" style="width: ${task.progress}%"></div>
                </div>
                <div class="progress-text">${task.progress.toFixed(1)}%</div>
            </div>
            <div class="task-step">${task.current_step}</div>
            ${task.error_message ? `<div class="task-error">${task.error_message}</div>` : ''}
            <div class="task-actions">${actionsHtml}</div>
        `;
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

function updateProviderDisplay() {
    const provider = document.getElementById('llmProvider').value;
    const displayText = document.querySelector('#llmProvider + span');

    let modelText = '';
    switch (provider) {
        case 'deepseek':
            modelText = 'DeepSeek V3.1 Terminus';
            break;
        case 'siliconflow':
            modelText = '硅基流动模型';
            break;
        case 'modelscope':
            modelText = '魔搭社区模型';
            break;
        case 'openrouter':
            modelText = 'OpenRouter模型';
            break;
        default:
            modelText = '未知模型';
    }

    displayText.textContent = '当前使用: ' + modelText;
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
                showSuccessMessage('连接成功！API密钥可用');
            } else {
                showDetailedErrorMessage('连接失败', [
                    'API密钥可能无效或已过期',
                    '请检查密钥是否正确复制',
                    '确认账户余额充足',
                    '尝试重新生成API密钥'
                ]);
            }
        } else {
            showDetailedErrorMessage('测试失败', [result.error]);
        }
    } catch (error) {
        console.error('连接测试错误:', error);
        showDetailedErrorMessage('网络错误', [
            '无法连接到服务器',
            '请检查网络连接',
            '错误详情: ' + error.message,
            '可能是防火墙或代理设置问题'
        ]);
    } finally {
        btn.textContent = '测试连接';
        btn.disabled = false;
    }
}

function showSuccessMessage(message) {
    alert('✅ ' + message);
}

function showDetailedErrorMessage(title, details) {
    const fullMessage = '❌ ' + title + '\n\n' +
                        '🔧 排查建议:\n' +
                        details.map((detail, index) => `${index + 1}. ${detail}`).join('\n');
    alert(fullMessage);
}

// 速度调节函数
function adjustVisitedSpeed(direction) {
    const select = document.getElementById('visitedSpeed');
    const options = Array.from(select.options);
    const currentIndex = select.selectedIndex;

    let newIndex = currentIndex + direction;
    if (newIndex < 0) newIndex = 0;
    if (newIndex >= options.length) newIndex = options.length - 1;

    select.selectedIndex = newIndex;
}

function adjustMovementSpeed(direction) {
    const select = document.getElementById('movementSpeed');
    const options = Array.from(select.options);
    const currentIndex = select.selectedIndex;

    let newIndex = currentIndex + direction;
    if (newIndex < 0) newIndex = 0;
    if (newIndex >= options.length) newIndex = options.length - 1;

    select.selectedIndex = newIndex;
}

function goToAlgorithmLibrary() {
    window.location.href = '/algorithm_library';
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
            showSuccessMessage('算法生成成功！DeepSeek V3.1 Terminus 已为您创建了高质量的寻路算法代码。');
            llmManager.loadCustomAlgorithms();
        } else {
            codeArea.value = '生成失败: ' + result.error;
            if (result.error.includes('API key') || result.error.includes('API密钥')) {
                showDetailedErrorMessage('API配置错误', [
                    '请先配置有效的API密钥',
                    '点击"测试连接"验证密钥是否可用',
                    '如果问题持续，尝试重新生成API密钥',
                    '也可以尝试切换到其他LLM提供商'
                ]);
            } else if (result.error.includes('network') || result.error.includes('网络')) {
                showDetailedErrorMessage('网络连接错误', [
                    '请检查网络连接是否正常',
                    '可能是网络不稳定导致请求失败',
                    '等待几分钟后重试',
                    '或尝试使用其他LLM提供商'
                ]);
            } else {
                showDetailedErrorMessage('算法生成失败', [
                    '错误信息: ' + result.error,
                    '请检查算法描述是否清晰明确',
                    '尝试使用更具体的技术术语',
                    '或简化描述重新生成'
                ]);
            }
        }
    } catch (error) {
        console.error('算法生成错误:', error);
        codeArea.value = '生成失败: ' + error.message;
        showDetailedErrorMessage('系统错误', [
            '系统发生了未知错误',
            '错误详情: ' + error.message,
            '请刷新页面后重试',
            '如果问题持续，请检查控制台日志'
        ]);
    } finally {
        generateBtn.textContent = '生成算法';
        generateBtn.disabled = false;
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
                this.updateGridCell(x, y);
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
                this.updateGridCell(x, y);
            }
            index--;
            setTimeout(animatePath, delay);
        } else {
            this.updateStatus('路径搜索完成');
        }
    };

    animatePath();
};

// 新增的LLM相关函数
function toggleGenerationMode() {
    const mode = document.querySelector('input[name="generationMode"]:checked').value;
    const generateBtn = document.getElementById('generateBtn');
    const smartGenerateBtn = document.getElementById('smartGenerateBtn');

    if (mode === 'simple') {
        generateBtn.style.display = 'inline-block';
        smartGenerateBtn.style.display = 'none';
    } else {
        generateBtn.style.display = 'none';
        smartGenerateBtn.style.display = 'inline-block';
    }
}

async function validateCurrentCode() {
    const code = document.getElementById('generatedCode').value.trim();
    const algorithmName = document.getElementById('algorithmName').value.trim() || 'CustomPathfindingAlgorithm';

    if (!code) {
        alert('请先生成或输入代码');
        return;
    }

    try {
        const response = await fetch('/llm/validate_code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                code: code,
                algorithm_name: algorithmName
            })
        });

        const result = await response.json();
        if (result.success) {
            displayValidationResult(result.validation_result);
        } else {
            showDetailedErrorMessage('验证失败', [result.error]);
        }
    } catch (error) {
        showDetailedErrorMessage('网络错误', [`验证请求失败: ${error.message}`]);
    }
}

function displayValidationResult(validationResult) {
    const resultDiv = document.getElementById('validationResult');
    const contentDiv = document.getElementById('validationContent');

    resultDiv.style.display = 'block';

    const errors = validationResult.errors;
    const warnings = validationResult.warnings;
    const suggestions = validationResult.suggestions;

    let html = '';

    // 总体评分
    const scoreColor = validationResult.overall_score >= 80 ? 'green' : validationResult.overall_score >= 60 ? 'orange' : 'red';
    html += `<div class="score-display">
        <h5>📊 综合评分: <span style="color: ${scoreColor}">${validationResult.overall_score.toFixed(1)}/100</span></h5>
        <p>${validationResult.is_valid ? '✅ 代码通过验证' : '❌ 代码存在问题'}</p>
    </div>`;

    // 错误
    if (errors.length > 0) {
        html += '<div class="validation-section errors">';
        html += '<h5>❌ 严重错误 (' + errors.length + ')</h5>';
        errors.forEach(error => {
            html += `<div class="validation-item">
                <div class="validation-message">${error.message}</div>
                ${error.line_number ? `<div class="validation-line">第 ${error.line_number} 行</div>` : ''}
                <div class="validation-suggestion">💡 建议: ${error.suggestion}</div>
            </div>`;
        });
        html += '</div>';
    }

    // 警告
    if (warnings.length > 0) {
        html += '<div class="validation-section warnings">';
        html += '<h5>⚠️ 警告 (' + warnings.length + ')</h5>';
        warnings.forEach(warning => {
            html += `<div class="validation-item">
                <div class="validation-message">${warning.message}</div>
                ${warning.line_number ? `<div class="validation-line">第 ${warning.line_number} 行</div>` : ''}
                <div class="validation-suggestion">💡 建议: ${warning.suggestion}</div>
            </div>`;
        });
        html += '</div>';
    }

    // 建议
    if (suggestions.length > 0) {
        html += '<div class="validation-section suggestions">';
        html += '<h5>💡 改进建议 (' + suggestions.length + ')</h5>';
        suggestions.forEach(suggestion => {
            html += `<div class="validation-item">
                <div class="validation-message">${suggestion.message}</div>
                ${suggestion.line_number ? `<div class="validation-line">第 ${suggestion.line_number} 行</div>` : ''}
                <div class="validation-suggestion">📝 ${suggestion.suggestion}</div>
            </div>`;
        });
        html += '</div>';
    }

    contentDiv.innerHTML = html;

    if (validationResult.is_valid) {
        showSuccessMessage('代码验证通过！可以保存使用。');
    }
}

async function fixCurrentCode() {
    const code = document.getElementById('generatedCode').value.trim();
    const algorithmName = document.getElementById('algorithmName').value.trim() || 'CustomPathfindingAlgorithm';
    const provider = document.getElementById('llmProvider').value;

    if (!code) {
        alert('请先生成或输入代码');
        return;
    }

    if (!confirm('开始智能修复代码？这可能需要一些时间。')) {
        return;
    }

    try {
        const response = await fetch('/llm/fix_code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                code: code,
                algorithm_name: algorithmName,
                provider: provider
            })
        });

        const result = await response.json();
        if (result.success) {
            showSuccessMessage('代码修复任务已启动！');
            llmManager.currentTaskId = result.task_id;
            toggleTaskMonitor(); // 自动打开任务监控面板
        } else {
            showDetailedErrorMessage('修复启动失败', [result.error]);
        }
    } catch (error) {
        showDetailedErrorMessage('网络错误', [`修复请求失败: ${error.message}`]);
    }
}

async function smartGenerateAlgorithm() {
    const description = document.getElementById('algorithmDescription').value.trim();
    const algorithmName = document.getElementById('algorithmName').value.trim();
    const provider = document.getElementById('llmProvider').value;

    if (!description) {
        alert('请输入算法描述');
        return;
    }

    if (!algorithmName) {
        alert('请输入算法名称');
        return;
    }

    const generateBtn = document.getElementById('smartGenerateBtn');
    const originalText = generateBtn.textContent;

    try {
        generateBtn.textContent = '智能生成中...';
        generateBtn.disabled = true;

        const response = await fetch('/llm/generate_and_fix_algorithm', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                description: description,
                name: algorithmName,
                provider: provider
            })
        });

        const result = await response.json();
        if (result.success) {
            showSuccessMessage('智能算法生成任务已启动！');
            llmManager.currentTaskId = result.task_id;
            toggleTaskMonitor(); // 自动打开任务监控面板
        } else {
            showDetailedErrorMessage('生成启动失败', [result.error]);
        }
    } catch (error) {
        showDetailedErrorMessage('网络错误', [`生成请求失败: ${error.message}`]);
    } finally {
        generateBtn.textContent = originalText;
        generateBtn.disabled = false;
    }
}

async function saveCurrentAlgorithm() {
    const code = document.getElementById('generatedCode').value.trim();
    const algorithmName = document.getElementById('algorithmName').value.trim();
    const description = document.getElementById('algorithmDescription').value.trim();

    if (!code) {
        alert('请先生成或输入代码');
        return;
    }

    if (!algorithmName) {
        alert('请输入算法名称');
        return;
    }

    try {
        const response = await fetch('/llm/save_algorithm', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: algorithmName,
                description: description,
                code: code
            })
        });

        const result = await response.json();
        if (result.success) {
            showSuccessMessage('算法保存成功！');
            llmManager.loadCustomAlgorithms(); // 刷新算法列表
        } else {
            showDetailedErrorMessage('保存失败', [result.error]);
        }
    } catch (error) {
        showDetailedErrorMessage('网络错误', [`保存请求失败: ${error.message}`]);
    }
}

// 任务监控相关函数
function toggleTaskMonitor() {
    const monitor = document.getElementById('taskMonitor');
    const btn = document.getElementById('taskMonitorBtn');

    if (monitor.style.display === 'none') {
        monitor.style.display = 'block';
        btn.textContent = '隐藏任务进度';
        refreshTasks(); // 刷新任务列表
    } else {
        monitor.style.display = 'none';
        btn.textContent = '查看任务进度';
    }
}

function hideTaskMonitor() {
    const monitor = document.getElementById('taskMonitor');
    const btn = document.getElementById('taskMonitorBtn');
    monitor.style.display = 'none';
    btn.textContent = '查看任务进度';
}

async function refreshTasks() {
    try {
        const response = await fetch('/tasks');
        const result = await response.json();

        if (result.success) {
            displayTasks(result.tasks);
        } else {
            console.error('获取任务列表失败:', result.error);
        }
    } catch (error) {
        console.error('刷新任务失败:', error);
    }
}

function displayTasks(tasks) {
    const container = document.getElementById('tasksContainer');

    if (tasks.length === 0) {
        container.innerHTML = '<div class="no-tasks">当前没有任务</div>';
        return;
    }

    // 按状态分组
    const activeTasks = tasks.filter(t => t.status === 'running' || t.status === 'paused');
    const completedTasks = tasks.filter(t => t.status === 'completed' || t.status === 'failed' || t.status === 'cancelled');

    let html = '';

    if (activeTasks.length > 0) {
        html += '<div class="task-section">';
        html += '<h4>🔄 活跃任务</h4>';
        activeTasks.forEach(task => {
            html += createTaskHTML(task);
        });
        html += '</div>';
    }

    if (completedTasks.length > 0) {
        html += '<div class="task-section">';
        html += '<h4>📋 已完成任务</h4>';
        completedTasks.forEach(task => {
            html += createTaskHTML(task);
        });
        html += '</div>';
    }

    container.innerHTML = html;
}

function createTaskHTML(task) {
    const statusColors = {
        pending: '#6b7280',
        running: '#3b82f6',
        paused: '#f59e0b',
        completed: '#10b981',
        failed: '#ef4444',
        cancelled: '#9ca3af'
    };

    const statusIcons = {
        pending: '⏳',
        running: '🔄',
        paused: '⏸️',
        completed: '✅',
        failed: '❌',
        cancelled: '🚫'
    };

    const color = statusColors[task.status] || '#6b7280';
    const icon = statusIcons[task.status] || '❓';

    const actions = [];
    if (task.status === 'running') {
        actions.push(`<button onclick="pauseTask('${task.task_id}')" class="btn-task">⏸️</button>`);
    } else if (task.status === 'paused') {
        actions.push(`<button onclick="resumeTask('${task.task_id}')" class="btn-task">▶️</button>`);
    }
    if (task.status === 'running' || task.status === 'paused') {
        actions.push(`<button onclick="cancelTask('${task.task_id}')" class="btn-task">🚫</button>`);
    }
    actions.push(`<button onclick="removeTask('${task.task_id}')" class="btn-task">🗑️</button>`);

    // 添加详细信息按钮（针对修复任务）
    let detailButton = '';
    if (task.task_type === 'FIXING' || task.task_type === 'GENERATION') {
        detailButton = `<button onclick="showTaskDetails('${task.task_id}')" class="btn-task" title="查看修复详情">📊</button>`;
        actions.splice(-1, 0, detailButton); // 在删除按钮前插入
    }

    // 生成详细的修复状态信息
    let detailHTML = '';
    if (task.task_type === 'FIXING' && task.fix_history) {
        detailHTML = createFixDetailHTML(task);
    }

    return `
        <div class="task-card" data-task-id="${task.task_id}" data-status="${task.status}">
            <div class="task-card-header">
                <div class="task-card-info">
                    <span class="task-icon">${icon}</span>
                    <span class="task-title">${task.title}</span>
                    ${task.task_type ? `<span class="task-type-badge">${getTaskTypeLabel(task.task_type)}</span>` : ''}
                </div>
                <div class="task-time">
                    ${task.elapsed_time.toFixed(1)}s
                    ${task.estimated_remaining_time ? `/ ${task.estimated_remaining_time.toFixed(1)}s` : ''}
                </div>
            </div>
            <div class="task-description">${task.description}</div>
            <div class="task-progress-bar">
                <div class="task-progress-track">
                    <div class="task-progress-fill" style="width: ${Math.min(task.progress, 100)}%; background-color: ${color}"></div>
                </div>
                <span class="task-progress-text">${Math.min(task.progress, 100).toFixed(1)}%</span>
            </div>
            <div class="task-step">${task.current_step}</div>

            <!-- 修复状态指标 -->
            ${task.errors_fixed !== undefined ? `
                <div class="fix-metrics">
                    <span class="fix-metric">✅ 修复错误: ${task.errors_fixed}</span>
                    <span class="fix-metric">⚡ 修复警告: ${task.warnings_fixed}</span>
                    ${task.iterations ? `<span class="fix-metric">🔄 迭代次数: ${task.iterations}</span>` : ''}
                </div>
            ` : ''}

            ${task.error_message ? `<div class="task-error">${task.error_message}</div>` : ''}
            ${detailHTML}
            <div class="task-actions">${actions.join('')}</div>
        </div>
    `;
}

function getTaskTypeLabel(taskType) {
    const labels = {
        'GENERATION': '🤖 生成',
        'FIXING': '🔧 修复',
        'VALIDATION': '🔍 验证'
    };
    return labels[taskType] || taskType;
}

function createFixDetailHTML(task) {
    if (!task.fix_history || task.fix_history.length === 0) {
        return '';
    }

    const latestFix = task.fix_history[task.fix_history.length - 1];
    let detailHTML = '<div class="task-details" style="display: none;">';

    detailHTML += '<div class="fix-history">';
    detailHTML += '<h5>🔧 修复历史记录</h5>';

    // 显示最近几次修复
    const recentFixes = task.fix_history.slice(-3).reverse();
    recentFixes.forEach((fix, index) => {
        const originalErrors = fix.original_validation.errors.length;
        const newErrors = fix.new_validation.errors.length;
        const errorsFixed = originalErrors - newErrors;
        const scoreImproved = fix.new_validation.overall_score - fix.original_validation.overall_score;

        detailHTML += `
            <div class="fix-iteration">
                <div class="fix-iteration-header">
                    <span class="fix-iteration-number">第 ${fix.iteration} 轮修复</span>
                    <span class="fix-iteration-time">${new Date().toLocaleTimeString()}</span>
                </div>
                <div class="fix-iteration-stats">
                    <span class="stat ${errorsFixed > 0 ? 'improved' : ''}">
                        错误: ${originalErrors} → ${newErrors} ${errorsFixed > 0 ? `(-${errorsFixed})` : ''}
                    </span>
                    <span class="stat ${scoreImproved > 0 ? 'improved' : ''}">
                        分数: ${fix.original_validation.overall_score.toFixed(1)} → ${fix.new_validation.overall_score.toFixed(1)} ${scoreImproved > 0 ? `(+${scoreImproved.toFixed(1)})` : ''}
                    </span>
                </div>
            </div>
        `;
    });

    detailHTML += '</div>';
    detailHTML += '</div>';

    return detailHTML;
}

async function showTaskDetails(taskId) {
    try {
        const response = await fetch(`/tasks/${taskId}`);
        const result = await response.json();

        if (result.success) {
            const task = result.task;
            const detailElement = document.querySelector(`[data-task-id="${taskId}"] .task-details`);

            if (detailElement) {
                if (detailElement.style.display === 'none') {
                    detailElement.style.display = 'block';
                    // 如果还没有详细信息，重新生成
                    if (detailElement.innerHTML.trim() === '') {
                        detailElement.innerHTML = createFixDetailHTML(task);
                    }
                } else {
                    detailElement.style.display = 'none';
                }
            }
        } else {
            alert('获取任务详情失败: ' + result.error);
        }
    } catch (error) {
        console.error('获取任务详情失败:', error);
    }
}

async function pauseTask(taskId) {
    try {
        const response = await fetch(`/tasks/${taskId}/pause`, { method: 'POST' });
        const result = await response.json();
        if (result.success) {
            refreshTasks();
        } else {
            alert('暂停失败: ' + result.error);
        }
    } catch (error) {
        alert('暂停请求失败: ' + error.message);
    }
}

async function resumeTask(taskId) {
    try {
        const response = await fetch(`/tasks/${taskId}/resume`, { method: 'POST' });
        const result = await response.json();
        if (result.success) {
            refreshTasks();
        } else {
            alert('恢复失败: ' + result.error);
        }
    } catch (error) {
        alert('恢复请求失败: ' + error.message);
    }
}

async function cancelTask(taskId) {
    if (!confirm('确定要取消这个任务吗？')) {
        return;
    }

    try {
        const response = await fetch(`/tasks/${taskId}/cancel`, { method: 'POST' });
        const result = await response.json();
        if (result.success) {
            refreshTasks();
            llmManager.currentTaskId = null;
        } else {
            alert('取消失败: ' + result.error);
        }
    } catch (error) {
        alert('取消请求失败: ' + error.message);
    }
}

async function removeTask(taskId) {
    if (!confirm('确定要移除这个任务记录吗？')) {
        return;
    }

    try {
        const response = await fetch(`/tasks/${taskId}/remove`, { method: 'DELETE' });
        const result = await response.json();
        if (result.success) {
            // 从DOM中移除任务元素
            const taskElement = document.getElementById(`task-${taskId}`);
            if (taskElement) {
                taskElement.remove();
            }
        } else {
            alert('移除失败: ' + result.error);
        }
    } catch (error) {
        alert('移除请求失败: ' + error.message);
    }
}

async function clearCompletedTasks() {
    if (!confirm('确定要清除所有已完成的任务记录吗？')) {
        return;
    }

    // 刷新任务列表，然后在客户端过滤掉已完成的任务
    const container = document.getElementById('tasksContainer');
    const taskCards = container.querySelectorAll('.task-card');

    taskCards.forEach(card => {
        const taskId = card.dataset.taskId;
        const taskStatus = card.querySelector('.task-icon').textContent;
        if (['✅', '❌', '🚫'].includes(taskStatus)) {
            card.remove();
        }
    });
}