"""
进度管理系统
提供可视化的任务进度跟踪和展示功能
"""

import time
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime


class TaskStatus(Enum):
    PENDING = "pending"       # 等待中
    RUNNING = "running"       # 运行中
    PAUSED = "paused"        # 已暂停
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"   # 已取消


class TaskType(Enum):
    VALIDATION = "validation"      # 验证任务
    GENERATION = "generation"      # 生成任务
    FIXING = "fixing"             # 修复任务
    OPTIMIZATION = "optimization" # 优化任务


@dataclass
class TaskProgress:
    """任务进度"""
    task_id: str
    task_type: TaskType
    status: TaskStatus
    title: str
    description: str
    progress: float  # 0-100
    current_step: str
    total_steps: int
    current_step_index: int
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['status'] = self.status.value
        data['task_type'] = self.task_type.value
        data['elapsed_time'] = self.get_elapsed_time()
        data['estimated_remaining_time'] = self.estimate_remaining_time()

        # 为修复任务添加额外的修复指标
        if self.result:
            errors_fixed = self.result.get('errors_fixed', 0)
            warnings_fixed = self.result.get('warnings_fixed', 0)
            iterations = self.result.get('iterations', 0)
            fix_history = self.result.get('fix_history', [])

            data['errors_fixed'] = errors_fixed
            data['warnings_fixed'] = warnings_fixed
            data['iterations'] = iterations
            data['fix_history'] = fix_history
        else:
            data['errors_fixed'] = 0
            data['warnings_fixed'] = 0
            data['iterations'] = 0
            data['fix_history'] = []

        return data

    def get_elapsed_time(self) -> float:
        """获取已用时间"""
        if not self.start_time:
            return 0
        end_time = self.end_time or time.time()
        return end_time - self.start_time

    def estimate_remaining_time(self) -> Optional[float]:
        """估算剩余时间"""
        if not self.start_time or self.progress <= 0:
            return None

        elapsed = self.get_elapsed_time()
        return (elapsed / self.progress) * (100 - self.progress) if self.progress < 100 else 0


class ProgressManager:
    """进度管理器"""

    def __init__(self):
        self.tasks: Dict[str, TaskProgress] = {}
        self.listeners: List[Callable[[TaskProgress], None]] = []
        self._lock = threading.Lock()

    def create_task(self, task_id: str, task_type: TaskType, title: str,
                   description: str = "", total_steps: int = 1) -> TaskProgress:
        """创建新任务"""
        with self._lock:
            task = TaskProgress(
                task_id=task_id,
                task_type=task_type,
                status=TaskStatus.PENDING,
                title=title,
                description=description,
                progress=0,
                current_step="",
                total_steps=total_steps,
                current_step_index=0
            )
            self.tasks[task_id] = task
            self._notify_listeners(task)
            return task

    def start_task(self, task_id: str) -> bool:
        """开始任务"""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return False

            task.status = TaskStatus.RUNNING
            task.start_time = time.time()
            self._notify_listeners(task)
            return True

    def update_progress(self, task_id: str, progress: float,
                       current_step: str = "", current_step_index: int = 0) -> bool:
        """更新任务进度"""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return False

            task.progress = max(0, min(100, progress))
            if current_step:
                task.current_step = current_step
            task.current_step_index = current_step_index

            self._notify_listeners(task)
            return True

    def update_step(self, task_id: str, step_index: int, step_name: str) -> bool:
        """更新当前步骤"""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return False

            task.current_step_index = step_index
            task.current_step = step_name
            task.progress = (step_index / task.total_steps) * 100

            self._notify_listeners(task)
            return True

    def complete_task(self, task_id: str, result: Optional[Dict[str, Any]] = None) -> bool:
        """完成任务"""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return False

            task.status = TaskStatus.COMPLETED
            task.progress = 100
            task.end_time = time.time()
            task.current_step_index = task.total_steps
            task.current_step = "已完成"
            task.result = result

            self._notify_listeners(task)
            return True

    def fail_task(self, task_id: str, error_message: str) -> bool:
        """任务失败"""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return False

            task.status = TaskStatus.FAILED
            task.end_time = time.time()
            task.error_message = error_message

            self._notify_listeners(task)
            return True

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return False

            task.status = TaskStatus.CANCELLED
            task.end_time = time.time()

            self._notify_listeners(task)
            return True

    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return False

            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.PAUSED
                self._notify_listeners(task)
                return True
            return False

    def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return False

            if task.status == TaskStatus.PAUSED:
                task.status = TaskStatus.RUNNING
                self._notify_listeners(task)
                return True
            return False

    def get_task(self, task_id: str) -> Optional[TaskProgress]:
        """获取任务"""
        with self._lock:
            task = self.tasks.get(task_id)
            return task

    def get_all_tasks(self) -> List[TaskProgress]:
        """获取所有任务"""
        with self._lock:
            return list(self.tasks.values())

    def get_active_tasks(self) -> List[TaskProgress]:
        """获取活跃任务"""
        with self._lock:
            return [task for task in self.tasks.values() if task.status == TaskStatus.RUNNING]

    def remove_task(self, task_id: str) -> bool:
        """移除任务"""
        with self._lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                return True
            return False

    def add_listener(self, listener: Callable[[TaskProgress], None]):
        """添加进度监听器"""
        self.listeners.append(listener)

    def remove_listener(self, listener: Callable[[TaskProgress], None]):
        """移除进度监听器"""
        if listener in self.listeners:
            self.listeners.remove(listener)

    def _notify_listeners(self, task: TaskProgress):
        """通知所有监听器"""
        for listener in self.listeners:
            try:
                listener(task)
            except Exception as e:
                print(f"Error in progress listener: {e}")

    def clear_completed_tasks(self, older_than_seconds: int = 3600):
        """清除已完成的旧任务"""
        with self._lock:
            current_time = time.time()
            tasks_to_remove = []

            for task_id, task in self.tasks.items():
                if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                    task.end_time and current_time - task.end_time > older_than_seconds):
                    tasks_to_remove.append(task_id)

            for task_id in tasks_to_remove:
                del self.tasks[task_id]


class HTMLProgressRenderer:
    """HTML进度渲染器"""

    def __init__(self, progress_manager: ProgressManager):
        self.progress_manager = progress_manager
        self.progress_manager.add_listener(self._on_progress_update)

    def _on_progress_update(self, task: TaskProgress):
        """进度更新回调"""
        # 这个方法会被任务进度更新时调用
        # 实际的HTML更新会在前端通过轮询或WebSocket实现
        pass

    def render_task_progress(self, task: TaskProgress) -> str:
        """渲染单个任务的进度"""
        status_colors = {
            TaskStatus.PENDING: "bg-gray-500",
            TaskStatus.RUNNING: "bg-blue-500",
            TaskStatus.PAUSED: "bg-yellow-500",
            TaskStatus.COMPLETED: "bg-green-500",
            TaskStatus.FAILED: "bg-red-500",
            TaskStatus.CANCELLED: "bg-gray-400"
        }

        status_icons = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.RUNNING: "🔄",
            TaskStatus.PAUSED: "⏸️",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.CANCELLED: "🚫"
        }

        color_class = status_colors.get(task.status, "bg-gray-500")
        icon = status_icons.get(task.status, "❓")

        elapsed_time = task.get_elapsed_time()
        remaining_time = task.estimate_remaining_time()

        time_str = f"已用: {elapsed_time:.1f}s"
        if remaining_time:
            time_str += f" | 预计剩余: {remaining_time:.1f}s"

        return f"""
        <div class="task-progress-card" data-task-id="{task.task_id}">
            <div class="task-header">
                <div class="task-title">
                    <span class="task-status-icon">{icon}</span>
                    <span class="task-name">{task.title}</span>
                </div>
                <div class="task-time">{time_str}</div>
            </div>

            <div class="task-description">{task.description}</div>

            <div class="progress-bar-container">
                <div class="progress-bar">
                    <div class="progress-fill {color_class}" style="width: {task.progress}%"></div>
                </div>
                <div class="progress-text">{task.progress:.1f}%</div>
            </div>

            <div class="task-step-info">
                <span class="current-step">{task.current_step}</span>
                <span class="step-counter">{task.current_step_index}/{task.total_steps}</span>
            </div>

            {f'<div class="task-error">❌ {task.error_message}</div>' if task.error_message and task.status == TaskStatus.FAILED else ''}

            {f'<div class="task-result">✅ 任务完成，包含结果数据</div>' if task.result and task.status == TaskStatus.COMPLETED else ''}

            <div class="task-actions">
                {'<button onclick="pauseTask(\'' + task.task_id + '\')" class="btn-pause">⏸️ 暂停</button>' if task.status == TaskStatus.RUNNING else ''}
                {'<button onclick="resumeTask(\'' + task.task_id + '\')" class="btn-resume">▶️ 继续</button>' if task.status == TaskStatus.PAUSED else ''}
                {'<button onclick="cancelTask(\'' + task.task_id + '\')" class="btn-cancel">🚫 取消</button>' if task.status in [TaskStatus.RUNNING, TaskStatus.PAUSED] else ''}
                <button onclick="removeTask(\'' + task.task_id + '\')" class="btn-remove">🗑️ 移除</button>
            </div>
        </div>
        """

    def render_all_tasks(self) -> str:
        """渲染所有任务"""
        tasks = self.progress_manager.get_all_tasks()

        if not tasks:
            return '<div class="no-tasks">当前没有任务</div>'

        active_tasks = [t for t in tasks if t.status in [TaskStatus.RUNNING, TaskStatus.PAUSED]]
        completed_tasks = [t for t in tasks if t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]]

        html = ""

        if active_tasks:
            html += '<h3>🔄 活跃任务</h3>'
            for task in active_tasks:
                html += self.render_task_progress(task)

        if completed_tasks:
            html += '<h3>📋 已完成任务</h3>'
            for task in sorted(completed_tasks, key=lambda t: t.end_time or 0, reverse=True):
                html += self.render_task_progress(task)

        return html


# 全局进度管理器实例
progress_manager = ProgressManager()

# 创建HTML渲染器实例
html_renderer = HTMLProgressRenderer(progress_manager)