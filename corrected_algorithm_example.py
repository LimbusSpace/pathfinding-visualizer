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
        简单易用的BFS寻路算法实现

        参数:
            grid: 二维数组，表示网格状态 (0: 空地, 1: 障碍物, 2: 起点, 3: 终点)
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
        获取访问节点的顺序

        返回:
            访问顺序列表 [(y1, x1), (y2, x2), ...]
        """
        return self.visited_order