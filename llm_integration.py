from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import re
import hashlib
import time
import requests
import json

class LLMProvider(Enum):
    MODELSCOPE = "modelscope"
    SILICONFLOW = "siliconflow"
    DEEPSEEK = "deepseek"
    OPENROUTER = "openrouter"

class LLMConfig:
    def __init__(self):
        self.api_keys = {
            LLMProvider.MODELSCOPE: "",
            LLMProvider.SILICONFLOW: "",
            LLMProvider.DEEPSEEK: "",
            LLMProvider.OPENROUTER: ""
        }
        self.api_urls = {
            LLMProvider.MODELSCOPE: "https://api.modelscope.cn/v1/chat/completions",
            LLMProvider.SILICONFLOW: "https://api.siliconflow.cn/v1/chat/completions",
            LLMProvider.DEEPSEEK: "https://api.deepseek.com/v1/chat/completions",
            LLMProvider.OPENROUTER: "https://openrouter.ai/api/v1/chat/completions"
        }
        self.models = {
            LLMProvider.MODELSCOPE: "deepseek-ai/DeepSeek-V3",
            LLMProvider.SILICONFLOW: "deepseek-ai/DeepSeek-V3.1-Terminus",
            LLMProvider.DEEPSEEK: "deepseek-chat",
            LLMProvider.OPENROUTER: "anthropic/claude-3.5-sonnet"
        }

    def set_api_key(self, provider: LLMProvider, api_key: str):
        self.api_keys[provider] = api_key.strip()

    def get_api_key(self, provider: LLMProvider) -> str:
        return self.api_keys.get(provider, "")

    def get_api_url(self, provider: LLMProvider) -> str:
        return self.api_urls.get(provider, "")

    def get_model(self, provider: LLMProvider) -> str:
        return self.models.get(provider, "")

    def is_provider_configured(self, provider: LLMProvider) -> bool:
        return bool(self.get_api_key(provider))

    def get_configured_providers(self) -> List[LLMProvider]:
        return [provider for provider in LLMProvider if self.is_provider_configured(provider)]

class LLMAlgorithmGenerator:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.current_provider = LLMProvider.SILICONFLOW

    def set_provider(self, provider: LLMProvider):
        if self.config.is_provider_configured(provider):
            self.current_provider = provider
        else:
            raise ValueError(f"Provider {provider.value} is not configured")

    def generate_algorithm_prompt(self, algorithm_description: str,
                                 grid_size: Tuple[int, int], start_pos: Tuple[int, int],
                                 end_pos: Tuple[int, int]) -> str:
        return f"""
You are a professional algorithm expert. Please generate a Python pathfinding algorithm based on the following requirements:

Algorithm description: {algorithm_description}
Grid size: {grid_size[0]}x{grid_size[1]}
Start position: {start_pos}
End position: {end_pos}

Please generate a complete Python class with the following methods:
1. __init__(self, width, height): Initialize the algorithm
2. find_path(self, grid, start, end): Main pathfinding method
3. get_visited_order(self): Get visit order

The algorithm should inherit from the following base class:

```python
from typing import List, Tuple, Optional
from enum import Enum

class CellType(Enum):
    EMPTY = 0
    WALL = 1
    START = 2
    END = 3
    VISITED = 4
    PATH = 5

class CustomPathfindingAlgorithm:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.visited_order = []

    def find_path(self, grid, start, end) -> List[Tuple[int, int]]:
        ```
        Main pathfinding method
        grid: 2D grid containing CellType enum values
        start: Start coordinate (row, col)
        end: End coordinate (row, col)
        return: Path coordinate list
        ```
        pass

    def get_visited_order(self) -> List[Tuple[int, int]]:
        ```
        Get the order of visited nodes
        return: Visit order list
        ```
        return self.visited_order
```

Requirements:
1. The algorithm must be a valid pathfinding algorithm that can avoid obstacles
2. Must record visit order for visualization
3. If a path is found, return the path coordinate list
4. If no path is found, return an empty list
5. The code must be complete and directly executable

Please return only the Python code, without any other explanations or comments.
"""

    def call_llm_api(self, prompt: str) -> Optional[str]:
        api_key = self.config.get_api_key(self.current_provider)
        if not api_key:
            return None

        try:
            if self.current_provider == LLMProvider.MODELSCOPE:
                return self._call_modelscope_api(prompt, api_key)
            elif self.current_provider == LLMProvider.SILICONFLOW:
                return self._call_siliconflow_api(prompt, api_key)
            elif self.current_provider == LLMProvider.DEEPSEEK:
                return self._call_deepseek_api(prompt, api_key)
            elif self.current_provider == LLMProvider.OPENROUTER:
                return self._call_openrouter_api(prompt, api_key)
        except Exception as e:
            print(f"LLM API call failed: {e}")
            return None

    def _call_modelscope_api(self, prompt: str, api_key: str) -> Optional[str]:
        url = self.config.get_api_url(LLMProvider.MODELSCOPE)
        model = self.config.get_model(LLMProvider.MODELSCOPE)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.7
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"ModelScope API call failed: {response.status_code} - {response.text}")
                return None
        except requests.RequestException as e:
            print(f"ModelScope network request failed: {e}")
            return None

    def _call_siliconflow_api(self, prompt: str, api_key: str) -> Optional[str]:
        url = self.config.get_api_url(LLMProvider.SILICONFLOW)
        model = self.config.get_model(LLMProvider.SILICONFLOW)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.7
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"SiliconFlow API call failed: {response.status_code} - {response.text}")
                return None
        except requests.RequestException as e:
            print(f"SiliconFlow network request failed: {e}")
            return None

    def _call_deepseek_api(self, prompt: str, api_key: str) -> Optional[str]:
        url = self.config.get_api_url(LLMProvider.DEEPSEEK)
        model = self.config.get_model(LLMProvider.DEEPSEEK)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.7
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"DeepSeek API call failed: {response.status_code} - {response.text}")
                return None
        except requests.RequestException as e:
            print(f"DeepSeek network request failed: {e}")
            return None

    def _call_openrouter_api(self, prompt: str, api_key: str) -> Optional[str]:
        url = self.config.get_api_url(LLMProvider.OPENROUTER)
        model = self.config.get_model(LLMProvider.OPENROUTER)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.7
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"OpenRouter API call failed: {response.status_code} - {response.text}")
                return None
        except requests.RequestException as e:
            print(f"OpenRouter network request failed: {e}")
            return None

    def generate_custom_algorithm(self, algorithm_description: str,
                                 grid_size: Tuple[int, int], start_pos: Tuple[int, int],
                                 end_pos: Tuple[int, int]) -> Optional[str]:
        prompt = self.generate_algorithm_prompt(
            algorithm_description, grid_size, start_pos, end_pos
        )

        code = self.call_llm_api(prompt)
        if code:
            code = self._clean_generated_code(code)
            return code
        return None

    def _clean_generated_code(self, code: str) -> str:
        code = re.sub(r'```python\n?', '', code)
        code = re.sub(r'```\n?', '', code)

        lines = code.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip() or (cleaned_lines and cleaned_lines[-1].strip()):
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def test_api_connection(self, provider: LLMProvider) -> bool:
        api_key = self.config.get_api_key(provider)
        if not api_key:
            return False

        test_prompt = "Please reply with 'API connection is normal'"
        try:
            if provider == LLMProvider.MODELSCOPE:
                result = self._call_modelscope_api(test_prompt, api_key)
            elif provider == LLMProvider.SILICONFLOW:
                result = self._call_siliconflow_api(test_prompt, api_key)
            elif provider == LLMProvider.DEEPSEEK:
                result = self._call_deepseek_api(test_prompt, api_key)
            elif provider == LLMProvider.OPENROUTER:
                result = self._call_openrouter_api(test_prompt, api_key)
            else:
                return False

            return result is not None
        except Exception as e:
            print(f"API connection test failed: {e}")
            return False

class CustomAlgorithmExecutor:
    def __init__(self):
        self.custom_algorithms = {}

    def load_algorithm(self, algorithm_name: str, algorithm_code: str, description: str = '') -> bool:
        try:
            namespace = {
                'List': list,
                'Tuple': tuple,
                'Optional': type(None),
                'Enum': Enum,
                'CellType': self._get_cell_type_enum()
            }

            exec(algorithm_code, namespace)

            for obj in namespace.values():
                if (hasattr(obj, '__name__') and
                    hasattr(obj, 'find_path') and
                    hasattr(obj, 'get_visited_order') and
                    callable(getattr(obj, 'find_path')) and
                    callable(getattr(obj, 'get_visited_order'))):
                    self.custom_algorithms[algorithm_name] = {
                        'class': obj,
                        'code': algorithm_code,
                        'description': description,
                        'created_at': time.time()
                    }
                    return True

            return False
        except Exception as e:
            print(f"Algorithm loading failed: {e}")
            return False

    def _get_cell_type_enum(self):
        class CellType(Enum):
            EMPTY = 0
            WALL = 1
            START = 2
            END = 3
            VISITED = 4
            PATH = 5
        return CellType

    def execute_algorithm(self, algorithm_name: str, width: int, height: int,
                         grid, start, end) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        if algorithm_name not in self.custom_algorithms:
            return [], []

        try:
            algorithm_class = self.custom_algorithms[algorithm_name]['class']
            algorithm_instance = algorithm_class(width, height)

            converted_grid = self._convert_grid(grid)

            path = algorithm_instance.find_path(converted_grid, start, end)
            visited_order = algorithm_instance.get_visited_order()

            return path, visited_order
        except Exception as e:
            print(f"Algorithm execution failed: {e}")
            return [], []

    def _convert_grid(self, grid):
        """将整数网格转换为CellType枚举网格"""
        # 使用与算法相同的CellType枚举定义
        class CellType(Enum):
            EMPTY = 0
            WALL = 1
            START = 2
            END = 3
            VISITED = 4
            PATH = 5

        try:
            converted = []
            for row in grid:
                converted_row = []
                for cell in row:
                    # 确保cell是整数类型
                    if isinstance(cell, CellType):
                        converted_row.append(cell)
                    else:
                        # 将整数转换为CellType枚举
                        converted_row.append(CellType(int(cell)))
                converted.append(converted_row)
            return converted
        except Exception as e:
            print(f"Grid conversion error: {e}")
            # 如果转换失败，返回一个安全的默认网格
            return [[CellType.EMPTY for _ in row] for row in grid]

    def get_available_algorithms(self) -> List[dict]:
        algorithms = []
        for name, info in self.custom_algorithms.items():
            algorithms.append({
                'name': name,
                'description': info.get('description', ''),
                'created_at': info.get('created_at', 0)
            })
        return algorithms

    def remove_algorithm(self, algorithm_name: str) -> bool:
        if algorithm_name in self.custom_algorithms:
            del self.custom_algorithms[algorithm_name]
            return True
        return False

llm_config = LLMConfig()
llm_generator = LLMAlgorithmGenerator(llm_config)
algorithm_executor = CustomAlgorithmExecutor()