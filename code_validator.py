"""
代码验证和检查机制
提供完整的代码分析、错误检测和修复建议功能
"""

import ast
import re
import traceback
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict


class ValidationLevel(Enum):
    CRITICAL = "critical"    # 严重错误，代码无法运行
    ERROR = "error"         # 错误，影响功能
    WARNING = "warning"     # 警告，可能存在问题
    INFO = "info"          # 信息，建议改进


@dataclass
class ValidationResult:
    """验证结果"""
    level: ValidationLevel
    message: str
    line_number: Optional[int] = None
    suggestion: str = ""
    code_snippet: str = ""


@dataclass
class CodeValidationResult:
    """代码验证完整结果"""
    is_valid: bool
    errors: List[ValidationResult]
    warnings: List[ValidationResult]
    suggestions: List[ValidationResult]
    overall_score: float  # 0-100 分

    def get_error_summary(self) -> str:
        """获取错误摘要"""
        if self.is_valid:
            return "✅ 代码验证通过"

        error_count = len(self.errors)
        warning_count = len(self.warnings)

        summary = f"❌ 代码验证失败\n"
        if error_count > 0:
            summary += f"严重错误: {error_count} 个\n"
        if warning_count > 0:
            summary += f"警告: {warning_count} 个\n"

        return summary


class CodeValidator:
    """代码验证器"""

    def __init__(self):
        self.required_methods = ['find_path', 'get_visited_order', '__init__']
        self.required_attributes = ['width', 'height', 'visited_order']

    def validate_algorithm_code(self, code: str, algorithm_name: str = "CustomPathfindingAlgorithm") -> CodeValidationResult:
        """验证算法代码的完整性"""
        errors = []
        warnings = []
        suggestions = []

        # 1. 基础语法检查
        syntax_errors = self._check_syntax(code)
        errors.extend(syntax_errors)

        if syntax_errors:
            return CodeValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                overall_score=0
            )

        # 2. 代码结构检查
        structure_errors = self._check_structure(code, algorithm_name)
        errors.extend(structure_errors)

        # 3. 方法签名检查
        method_errors = self._check_method_signatures(code, algorithm_name)
        errors.extend(method_errors)

        # 4. 代码逻辑检查
        logic_errors = self._check_logic(code)
        errors.extend(logic_errors)

        # 5. 语法规范检查
        syntax_errors = self._check_syntax_standards(code)
        errors.extend(syntax_errors)

        # 6. 最佳实践建议
        practice_suggestions = self._check_best_practices(code)
        suggestions.extend(practice_suggestions)

        # 7. 性能和兼容性检查
        perf_warnings = self._check_performance(code)
        warnings.extend(perf_warnings)

        # 计算总分
        score = self._calculate_score(errors, warnings, suggestions)

        return CodeValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            overall_score=score
        )

    def _check_syntax(self, code: str) -> List[ValidationResult]:
        """检查语法错误"""
        errors = []

        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(ValidationResult(
                level=ValidationLevel.CRITICAL,
                message=f"语法错误: {e.msg}",
                line_number=e.lineno,
                suggestion="检查代码语法，确保括号、引号等配对正确",
                code_snippet=self._get_line_snippet(code, e.lineno)
            ))
        except Exception as e:
            errors.append(ValidationResult(
                level=ValidationLevel.CRITICAL,
                message=f"语法解析失败: {str(e)}",
                suggestion="请检查代码完整性"
            ))

        return errors

    def _check_structure(self, code: str, algorithm_name: str) -> List[ValidationResult]:
        """检查代码结构"""
        errors = []

        try:
            tree = ast.parse(code)

            # 查找目标类
            target_class = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == algorithm_name:
                    target_class = node
                    break

            if not target_class:
                errors.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    message=f"找不到类定义: {algorithm_name}",
                    suggestion=f"确保定义了 {algorithm_name} 类"
                ))
                return errors

            # 检查必需方法
            method_names = []
            for node in target_class.body:
                if isinstance(node, ast.FunctionDef):
                    method_names.append(node.name)

            for required_method in self.required_methods:
                if required_method not in method_names:
                    errors.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        message=f"缺少必需方法: {required_method}",
                        suggestion=f"在类中添加 {required_method} 方法"
                    ))

        except Exception as e:
            errors.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"结构检查失败: {str(e)}"
            ))

        return errors

    def _check_method_signatures(self, code: str, algorithm_name: str) -> List[ValidationResult]:
        """检查方法签名"""
        errors = []

        expected_signatures = {
            'find_path': ['self', 'grid', 'start', 'end'],
            'get_visited_order': ['self'],
            '__init__': ['self', 'width', 'height']
        }

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == algorithm_name:
                    for class_node in node.body:
                        if isinstance(class_node, ast.FunctionDef):
                            method_name = class_node.name
                            if method_name in expected_signatures:
                                # 检查参数
                                actual_args = [arg.arg for arg in class_node.args.args]
                                expected_args = expected_signatures[method_name]

                                if actual_args != expected_args:
                                    errors.append(ValidationResult(
                                        level=ValidationLevel.ERROR,
                                        message=f"方法 {method_name} 参数不正确",
                                        suggestion=f"期望参数: {expected_args}, 实际参数: {actual_args}"
                                    ))

        except Exception as e:
            errors.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"方法签名检查失败: {str(e)}"
            ))

        return errors

    def _check_logic(self, code: str) -> List[ValidationResult]:
        """检查代码逻辑"""
        errors = []

        # 检查是否有无限循环的风险
        if "while True:" in code:
            errors.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="发现可能的无限循环",
                suggestion="确保有适当的循环退出条件，如 if condition: break"
            ))

        # 检查是否处理了无路径情况
        if "find_path" in code and "return []" not in code:
            errors.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="可能缺少无路径情况处理",
                suggestion="在 find_path 方法中添加无路径时的返回值，如 return []"
            ))

        # 检查是否记录了访问顺序
        if "visited_order" not in code:
            errors.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message="缺少访问顺序记录",
                suggestion="确保在算法中添加 visited_order 列表并记录访问的节点"
            ))

        # 检查是否正确处理了grid参数
        if "find_path" in code and "grid[" not in code:
            errors.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="可能没有正确使用grid参数",
                suggestion="确保在算法中使用传入的grid参数检查障碍物"
            ))

        # 增强的逻辑检查
        # 检查变量类型规范
        if "self.visited_order" in code and "self.visited_order = []" not in code:
            errors.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="visited_order 初始化可能不规范",
                suggestion="在 __init__ 方法中添加 self.visited_order = []"
            ))

        # 检查方法返回值类型
        if "def get_visited_order(self)" in code and "return self.visited_order" not in code:
            errors.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="get_visited_order 方法返回值不规范",
                suggestion="确保 get_visited_order 方法返回 self.visited_order"
            ))

        # 检查坐标格式规范
        if "find_path" in code and "(y, x)" not in code and "(x, y)" in code:
            errors.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="建议使用 (y, x) 坐标格式",
                suggestion="为了保持一致性，建议使用 (y, x) 格式表示坐标"
            ))

        # 检查网格边界检查
        if "find_path" in code and ("0 >=" not in code and ">=" not in code.split("find_path")[1].split("def")[0]):
            errors.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="可能缺少网格边界检查",
                suggestion="确保在访问 grid[y][x] 前检查坐标范围: 0 <= y < height and 0 <= x < width"
            ))

        # 检查算法核心逻辑
        if "find_path" in code and ("queue" not in code and "stack" not in code and "list" not in code):
            errors.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="算法可能缺少必要的数据结构",
                suggestion="寻路算法通常需要队列、栈或列表等数据结构来管理节点"
            ))

        return errors

    def _check_syntax_standards(self, code: str) -> List[ValidationResult]:
        """检查语法规范标准"""
        errors = []

        # 检查Python版本兼容性
        if "print " in code and "print(" not in code:
            errors.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message="使用了Python 2的print语法",
                suggestion="请使用Python 3的print函数语法：print()"
            ))

        # 检查导入语句规范
        import_lines = [line for line in code.split('\n') if line.strip().startswith('import ') or line.strip().startswith('from ')]
        for line in import_lines:
            if 'import *' in line:
                errors.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    message="使用了通配符导入",
                    suggestion="避免使用 import *，明确导入需要的模块"
                ))

        # 检查命名规范
        class_match = re.search(r'class\s+(\w+)', code)
        if class_match and not class_match.group(1)[0].isupper():
            errors.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="类名不符合驼峰命名规范",
                suggestion="类名应该使用驼峰命名法，如：MyClass"
            ))

        # 检查方法命名规范
        method_matches = re.findall(r'def\s+(\w+)\(', code)
        for method_name in method_matches:
            if not method_name.islower() and '_' not in method_name:
                errors.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    message=f"方法名 {method_name} 不符合蛇形命名规范",
                    suggestion="方法名应该使用蛇形命名法，如：my_method"
                ))

        # 检查空行规范
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if line.strip().endswith(':') and i + 1 <= len(lines):
                next_line = lines[i] if i < len(lines) else ""
                if not next_line.strip() or not next_line.startswith('    '):
                    errors.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        message=f"第 {i} 行后缩进不规范",
                        suggestion="冒号后应该有空行或正确缩进"
                    ))

        return errors

    def _check_best_practices(self, code: str) -> List[ValidationResult]:
        """检查最佳实践"""
        suggestions = []

        # 检查是否使用了类型注解
        if "def find_path(" in code and "->" not in code.split("def find_path(")[1].split("\n")[0]:
            suggestions.append(ValidationResult(
                level=ValidationLevel.INFO,
                message="建议添加类型注解",
                suggestion="为方法和变量添加类型注解，提高代码可读性"
            ))

        # 检查是否有文档字符串
        if '"""' not in code and "'''" not in code:
            suggestions.append(ValidationResult(
                level=ValidationLevel.INFO,
                message="建议添加文档字符串",
                suggestion="为类和方法添加详细文档"
            ))

        # 检查异常处理
        if "try:" not in code and "except" not in code and "find_path" in code:
            suggestions.append(ValidationResult(
                level=ValidationLevel.INFO,
                message="建议添加异常处理",
                suggestion="为关键操作添加 try-except 块处理可能的异常"
            ))

        # 检查常量定义
        if "0 ==" in code or "1 ==" in code:
            suggestions.append(ValidationResult(
                level=ValidationLevel.INFO,
                message="建议使用有意义的常量",
                suggestion="定义有意义的常量替代魔数，如：WALL = 1"
            ))

        # 检查列表推导式使用
        if "for i in range(len(" in code:
            suggestions.append(ValidationResult(
                level=ValidationLevel.INFO,
                message="建议使用更Pythonic的循环方式",
                suggestion="考虑使用 enumerate() 或列表推导式替代 range(len())"
            ))

        return suggestions

    def _check_performance(self, code: str) -> List[ValidationResult]:
        """检查性能问题"""
        warnings = []

        # 检查是否有低效的数据结构使用
        if "list.index(" in code:
            warnings.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="潜在的效率问题: 使用 list.index()",
                suggestion="考虑使用字典或其他数据结构提高查找效率"
            ))

        return warnings

    def _get_line_snippet(self, code: str, line_number: int) -> str:
        """获取指定行的代码片段"""
        if not line_number:
            return ""

        lines = code.split('\n')
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1].strip()
        return ""

    def _calculate_score(self, errors: List[ValidationResult], warnings: List[ValidationResult], suggestions: List[ValidationResult]) -> float:
        """计算验证分数"""
        error_weight = 10
        warning_weight = 3
        suggestion_weight = 1

        deductions = (
            len(errors) * error_weight +
            len(warnings) * warning_weight +
            len(suggestions) * suggestion_weight
        )

        score = max(0, 100 - deductions)
        return score


class CodeFixer:
    """代码修复建议生成器"""

    def __init__(self):
        self.validator = CodeValidator()

    def generate_fix_suggestions(self, validation_result: CodeValidationResult, original_code: str) -> Dict[str, Any]:
        """生成修复建议"""
        fix_suggestions = {
            "critical_fixes": [],
            "error_fixes": [],
            "warning_fixes": [],
            "suggestion_fixes": [],
            "improved_code": None
        }

        # 按优先级生成修复建议
        for error in validation_result.errors:
            fix_suggestions["critical_fixes"].append({
                "issue": error.message,
                "line": error.line_number,
                "fix": self._generate_fix_for_error(error),
                "priority": "high"
            })

        for warning in validation_result.warnings:
            fix_suggestions["warning_fixes"].append({
                "issue": warning.message,
                "line": warning.line_number,
                "fix": self._generate_fix_for_error(warning),
                "priority": "medium"
            })

        for suggestion in validation_result.suggestions:
            fix_suggestions["suggestion_fixes"].append({
                "issue": suggestion.message,
                "line": suggestion.line_number,
                "fix": suggestion.suggestion,
                "priority": "low"
            })

        return fix_suggestions

    def _generate_fix_for_error(self, error: ValidationResult) -> str:
        """为特定错误生成修复建议"""
        error_msg = error.message.lower()

        if "语法错误" in error_msg:
            return f"请检查并修复语法错误: {error.message}"
        elif "缺少" in error_msg and "方法" in error_msg:
            return f"请添加缺少的方法"
        elif "参数不正确" in error_msg:
            return f"请修正方法参数: {error.suggestion}"
        elif "访问顺序" in error_msg:
            return "请在算法中添加 visited_order 的记录逻辑"
        elif "文档字符串" in error_msg:
            return "请为类和方法添加文档字符串"
        else:
            return error.suggestion or "请仔细检查代码逻辑"


# 测试函数
def test_code_validator():
    """测试代码验证器"""
    validator = CodeValidator()

    # 测试代码
    test_code = '''
from typing import List, Tuple, Optional
from enum import Enum

class CustomPathfindingAlgorithm:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.visited_order = []

    def find_path(self, grid, start, end) -> List[Tuple[int, int]]:
        if start == end:
            return [start]

        # 简单的BFS实现
        from collections import deque
        queue = deque([start])
        visited = set([start])
        parent = {start: None}

        self.visited_order = [start]

        while queue:
            current = queue.popleft()
            if current == end:
                path = []
                while current:
                    path.append(current)
                    current = parent[current]
                path.reverse()
                return path

            y, x = current
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = y + dy, x + dx
                neighbor = (ny, nx)
                if (0 <= ny < self.height and 0 <= nx < self.width and
                    neighbor not in visited and grid[ny][nx] != 1):
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)
                    self.visited_order.append(neighbor)

        return []

    def get_visited_order(self) -> List[Tuple[int, int]]:
        return self.visited_order
'''

    result = validator.validate_algorithm_code(test_code)
    print(f"验证结果: {result.is_valid}")
    print(f"分数: {result.overall_score}")
    print(f"错误数量: {len(result.errors)}")
    print(f"警告数量: {len(result.warnings)}")
    print(f"建议数量: {len(result.suggestions)}")

    for error in result.errors:
        print(f"错误: {error.message}")

    return result


if __name__ == "__main__":
    test_code_validator()