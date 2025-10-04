import heapq
import math
from typing import List, Tuple, Set, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class CellType(Enum):
    EMPTY = 0
    WALL = 1
    START = 2
    END = 3
    PATH = 4
    VISITED = 5
    FRONTIER = 6

@dataclass
class Node:
    x: int
    y: int
    g: float = 0
    h: float = 0
    f: float = 0
    parent: Optional['Node'] = None

    def __lt__(self, other):
        return self.f < other.f

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

class PathfindingAlgorithm:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[CellType.EMPTY for _ in range(width)] for _ in range(height)]
        self.start = None
        self.end = None
        self.visited_order = []

    def set_grid(self, grid_data: List[List[int]]):
        """设置网格数据"""
        self.grid = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append(CellType(grid_data[y][x]))
                if grid_data[y][x] == CellType.START.value:
                    self.start = (x, y)
                elif grid_data[y][x] == CellType.END.value:
                    self.end = (x, y)
            self.grid.append(row)

    def get_neighbors(self, x: int, y: int, diagonal: bool = False) -> List[Tuple[int, int]]:
        """获取邻居节点"""
        neighbors = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # 上下左右

        if diagonal:
            directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])  # 对角线

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if (0 <= nx < self.width and 0 <= ny < self.height and
                self.grid[ny][nx] != CellType.WALL):
                neighbors.append((nx, ny))

        return neighbors

    def heuristic(self, a: Tuple[int, int], b: Tuple[int, int], method: str = "manhattan") -> float:
        """启发式函数"""
        x1, y1 = a
        x2, y2 = b

        if method == "manhattan":
            return abs(x1 - x2) + abs(y1 - y2)
        elif method == "euclidean":
            return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
        else:  # diagonal
            return max(abs(x1 - x2), abs(y1 - y2))

    def reconstruct_path(self, node: Node) -> List[Tuple[int, int]]:
        """重构路径"""
        path = []
        current = node
        while current is not None:
            path.append((current.x, current.y))
            current = current.parent
        return path[::-1]

    def astar(self, diagonal: bool = False, heuristic_method: str = "manhattan") -> Dict:
        """A*寻路算法"""
        if not self.start or not self.end:
            return {"path": [], "visited": [], "found": False}

        open_set = []
        closed_set = set()
        visited_nodes = []

        start_node = Node(self.start[0], self.start[1])
        start_node.h = self.heuristic(self.start, self.end, heuristic_method)
        start_node.f = start_node.h

        heapq.heappush(open_set, start_node)

        while open_set:
            current = heapq.heappop(open_set)

            if (current.x, current.y) in closed_set:
                continue

            closed_set.add((current.x, current.y))
            visited_nodes.append((current.x, current.y))

            if (current.x, current.y) == self.end:
                path = self.reconstruct_path(current)
                return {
                    "path": path,
                    "visited": visited_nodes,
                    "found": True
                }

            for nx, ny in self.get_neighbors(current.x, current.y, diagonal):
                if (nx, ny) in closed_set:
                    continue

                tentative_g = current.g + (1.4 if diagonal and abs(nx - current.x) + abs(ny - current.y) > 1 else 1)

                neighbor_node = Node(nx, ny, tentative_g, 0, 0, current)
                neighbor_node.h = self.heuristic((nx, ny), self.end, heuristic_method)
                neighbor_node.f = neighbor_node.g + neighbor_node.h

                # 检查是否在开放集合中
                in_open_set = False
                for i, node in enumerate(open_set):
                    if node.x == nx and node.y == ny:
                        if tentative_g < node.g:
                            open_set[i] = neighbor_node
                            heapq.heapify(open_set)
                        in_open_set = True
                        break

                if not in_open_set:
                    heapq.heappush(open_set, neighbor_node)

        return {"path": [], "visited": visited_nodes, "found": False}

    def dijkstra(self) -> Dict:
        """Dijkstra寻路算法"""
        if not self.start or not self.end:
            return {"path": [], "visited": [], "found": False}

        distances = [[float('inf')] * self.width for _ in range(self.height)]
        previous = [[None] * self.width for _ in range(self.height)]
        visited = set()
        unvisited = []

        start_x, start_y = self.start
        distances[start_y][start_x] = 0
        heapq.heappush(unvisited, (0, start_x, start_y))

        while unvisited:
            current_dist, x, y = heapq.heappop(unvisited)

            if (x, y) in visited:
                continue

            visited.add((x, y))

            if (x, y) == self.end:
                # 重构路径
                path = []
                current_x, current_y = x, y
                while previous[current_y][current_x] is not None:
                    path.append((current_x, current_y))
                    current_x, current_y = previous[current_y][current_x]
                path.append(self.start)
                return {
                    "path": path[::-1],
                    "visited": list(visited),
                    "found": True
                }

            for nx, ny in self.get_neighbors(x, y):
                if (nx, ny) in visited:
                    continue

                alt_distance = current_dist + 1
                if alt_distance < distances[ny][nx]:
                    distances[ny][nx] = alt_distance
                    previous[ny][nx] = (x, y)
                    heapq.heappush(unvisited, (alt_distance, nx, ny))

        return {"path": [], "visited": list(visited), "found": False}

    def bfs(self) -> Dict:
        """广度优先搜索"""
        if not self.start or not self.end:
            return {"path": [], "visited": [], "found": False}

        from collections import deque

        queue = deque([self.start])
        visited = set([self.start])
        previous = {}

        while queue:
            x, y = queue.popleft()

            if (x, y) == self.end:
                # 重构路径
                path = []
                current = (x, y)
                while current in previous:
                    path.append(current)
                    current = previous[current]
                path.append(self.start)
                return {
                    "path": path[::-1],
                    "visited": list(visited),
                    "found": True
                }

            for nx, ny in self.get_neighbors(x, y):
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    previous[(nx, ny)] = (x, y)
                    queue.append((nx, ny))

        return {"path": [], "visited": list(visited), "found": False}