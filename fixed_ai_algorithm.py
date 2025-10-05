from typing import List, Tuple, Optional
from enum import Enum
from collections import deque

class CustomPathfindingAlgorithm:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.visited_order = []

    def find_path(self, grid, start, end) -> List[Tuple[int, int]]:
        """
        修正后的AI算法 - BFS + 一些优化

        参数:
            grid: 二维数组，0=空地, 1=障碍物, 2=起点, 3=终点
            start: 起点坐标 (y, x)
            end: 终点坐标 (y, x)

        返回:
            路径坐标列表
        """
        start_y, start_x = start
        end_y, end_x = end

        if start == end:
            return [start]

        def is_valid(y, x):
            return (0 <= y < self.height and
                    0 <= x < self.width and
                    grid[y][x] != 1)  # 1 是障碍物

        def get_neighbors(y, x):
            neighbors = []
            # 四个方向
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

            for dy, dx in directions:
                ny, nx = y + dy, x + dx
                if is_valid(ny, nx):
                    neighbors.append((ny, nx))
            return neighbors

        def jump(y, x, dy, dx):
            """
            简化的跳跃点搜索
            """
            ny, nx = y + dy, x + dx

            # 检查是否到达终点
            if (ny, nx) == end:
                return [(ny, nx)]

            # 检查是否越界或遇到障碍物
            if not is_valid(ny, nx):
                return []

            # 检查是否有强迫邻居
            has_forced_neighbor = False

            if dy != 0:  # 垂直移动
                # 检查左右邻居
                if is_valid(ny, nx - 1) and not is_valid(ny - dy, nx - 1):
                    has_forced_neighbor = True
                if is_valid(ny, nx + 1) and not is_valid(ny - dy, nx + 1):
                    has_forced_neighbor = True
            else:  # 水平移动
                # 检查上下邻居
                if is_valid(ny - 1, nx) and not is_valid(ny - 1, nx - dx):
                    has_forced_neighbor = True
                if is_valid(ny + 1, nx) and not is_valid(ny + 1, nx - dx):
                    has_forced_neighbor = True

            # 如果有强迫邻居，返回当前点作为跳跃点
            if has_forced_neighbor:
                return [(ny, nx)]

            # 尝试继续跳跃
            return jump(ny, nx, dy, dx)

        # 使用优先队列，优先考虑距离终点更近的点
        def heuristic(y, x):
            return abs(y - end_y) + abs(x - end_x)

        import heapq
        # 优先队列: (优先级, y, x, 父节点)
        heap = [(0, start_y, start_x, None)]

        visited = set()
        parent_map = {}
        self.visited_order = []

        while heap:
            priority, y, x, parent = heapq.heappop(heap)
            current = (y, x)

            if current in visited:
                continue

            visited.add(current)
            self.visited_order.append(current)
            parent_map[current] = parent

            if current == end:
                # 重建路径
                path = []
                while current is not None:
                    path.append(current)
                    current = parent_map[current]
                path.reverse()
                return path

            # 尝试跳跃点搜索
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                jump_result = jump(y, x, dy, dx)

                if jump_result:
                    for jump_point in jump_result:
                        if jump_point not in visited:
                            jump_y, jump_x = jump_point
                            jump_priority = heuristic(jump_y, jump_x)
                            heapq.heappush(heap, (jump_priority, jump_y, jump_x, current))

            # 如果没有找到跳跃点，使用常规BFS
            for neighbor in get_neighbors(y, x):
                if neighbor not in visited:
                    ny, nx = neighbor
                    neighbor_priority = heuristic(ny, nx)
                    heapq.heappush(heap, (neighbor_priority, ny, nx, current))

        return []  # 未找到路径

    def get_visited_order(self) -> List[Tuple[int, int]]:
        """获取访问顺序"""
        return self.visited_order