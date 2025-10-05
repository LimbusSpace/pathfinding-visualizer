"""
LLM错误驱动的代码修复系统
基于代码验证结果，让LLM迭代修复代码错误
"""

import time
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import requests

from code_validator import CodeValidator, CodeValidationResult, ValidationResult, ValidationLevel
from llm_integration import LLMProvider, LLMConfig


class FixStep(Enum):
    ANALYSIS = "analysis"        # 分析错误
    GENERATION = "generation"    # 生成修复代码
    VALIDATION = "validation"    # 验证修复结果
    OPTIMIZATION = "optimization" # 优化和改进


@dataclass
class FixProgress:
    """修复进度"""
    current_step: FixStep
    total_steps: int
    current_iteration: int
    max_iterations: int
    step_progress: float  # 0-100
    message: str
    start_time: float
    errors_fixed: int = 0
    warnings_fixed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_step": self.current_step.value,
            "current_step_name": self._get_step_name(),
            "total_steps": self.total_steps,
            "current_iteration": self.current_iteration,
            "max_iterations": self.max_iterations,
            "step_progress": self.step_progress,
            "message": self.message,
            "elapsed_time": time.time() - self.start_time,
            "errors_fixed": self.errors_fixed,
            "warnings_fixed": self.warnings_fixed,
            "overall_progress": self._calculate_overall_progress()
        }

    def _get_step_name(self) -> str:
        step_names = {
            FixStep.ANALYSIS: "🔍 分析错误",
            FixStep.GENERATION: "🔧 生成修复代码",
            FixStep.VALIDATION: "✅ 验证修复结果",
            FixStep.OPTIMIZATION: "⚡ 优化和改进"
        }
        return step_names.get(self.current_step, "未知步骤")

    def _calculate_overall_progress(self) -> float:
        """计算总体进度"""
        iteration_progress = (self.current_iteration - 1) / self.max_iterations
        step_progress = list(FixStep).index(self.current_step) / len(FixStep)
        return (iteration_progress + step_progress / self.max_iterations) * 100


class LLMCodeFixer:
    """LLM代码修复器"""

    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.validator = CodeValidator()
        self.current_provider = LLMProvider.DEEPSEEK
        self.max_iterations = 5  # 最大迭代次数
        self.fix_history = []  # 修复历史

    def set_provider(self, provider: LLMProvider):
        """设置LLM提供商"""
        if self.llm_config.is_provider_configured(provider):
            self.current_provider = provider
        else:
            raise ValueError(f"Provider {provider.value} is not configured")

    def fix_algorithm_code(self, original_code: str, algorithm_name: str = "CustomPathfindingAlgorithm",
                          progress_callback=None) -> Dict[str, Any]:
        """修复算法代码"""

        # 初始化进度
        progress = FixProgress(
            current_step=FixStep.ANALYSIS,
            total_steps=len(FixStep),
            current_iteration=1,
            max_iterations=self.max_iterations,
            step_progress=0,
            message="开始代码修复过程",
            start_time=time.time()
        )

        if progress_callback:
            progress_callback(progress.to_dict())

        self.fix_history = []
        current_code = original_code

        for iteration in range(1, self.max_iterations + 1):
            progress.current_iteration = iteration
            progress.message = f"开始第 {iteration} 轮修复"

            if progress_callback:
                progress_callback(progress.to_dict())

            try:
                # 步骤1: 分析错误
                progress.current_step = FixStep.ANALYSIS
                progress.step_progress = 0
                progress.message = "🔍 分析代码错误..."

                if progress_callback:
                    progress_callback(progress.to_dict())

                validation_result = self.validator.validate_algorithm_code(current_code, algorithm_name)

                progress.step_progress = 100
                progress.message = f"发现 {len(validation_result.errors)} 个错误，{len(validation_result.warnings)} 个警告"

                if progress_callback:
                    progress_callback(progress.to_dict())

                # 如果代码已经验证通过，结束修复
                if validation_result.is_valid:
                    progress.current_step = FixStep.OPTIMIZATION
                    progress.step_progress = 100
                    progress.message = "✅ 代码修复成功！现在进行优化..."

                    if progress_callback:
                        progress_callback(progress.to_dict())

                    # 最终优化
                    optimized_code = self._optimize_code(current_code, progress_callback)

                    return {
                        "success": True,
                        "final_code": optimized_code,
                        "original_code": original_code,
                        "iterations": iteration,
                        "validation_result": asdict(validation_result),
                        "fix_history": self.fix_history,
                        "elapsed_time": time.time() - progress.start_time
                    }

                # 步骤2: 生成修复代码
                progress.current_step = FixStep.GENERATION
                progress.step_progress = 0
                progress.message = "🔧 生成修复代码..."

                if progress_callback:
                    progress_callback(progress.to_dict())

                # 生成修复提示
                fix_prompt = self._generate_fix_prompt(current_code, validation_result, iteration)

                # 调用LLM修复代码
                fixed_code = self._call_llm_for_fix(fix_prompt)

                if not fixed_code:
                    raise Exception("LLM返回空结果")

                progress.step_progress = 100
                progress.message = "✅ 修复代码生成完成"

                if progress_callback:
                    progress_callback(progress.to_dict())

                # 步骤3: 验证修复结果
                progress.current_step = FixStep.VALIDATION
                progress.step_progress = 0
                progress.message = "✅ 验证修复结果..."

                if progress_callback:
                    progress_callback(progress.to_dict())

                new_validation_result = self.validator.validate_algorithm_code(fixed_code, algorithm_name)

                # 记录修复历史
                fix_record = {
                    "iteration": iteration,
                    "original_code": current_code,
                    "fixed_code": fixed_code,
                    "original_validation": asdict(validation_result),
                    "new_validation": asdict(new_validation_result),
                    "improvements": self._calculate_improvements(validation_result, new_validation_result)
                }
                self.fix_history.append(fix_record)

                # 更新进度统计
                progress.errors_fixed = len(validation_result.errors) - len(new_validation_result.errors)
                progress.warnings_fixed = len(validation_result.warnings) - len(new_validation_result.warnings)

                progress.step_progress = 100
                progress.message = f"验证完成: 错误减少 {progress.errors_fixed} 个，警告减少 {progress.warnings_fixed} 个"

                if progress_callback:
                    progress_callback(progress.to_dict())

                # 更新当前代码
                current_code = fixed_code

            except Exception as e:
                progress.current_step = FixStep.ANALYSIS
                progress.step_progress = 0
                progress.message = f"❌ 第 {iteration} 轮修复失败: {str(e)}"

                if progress_callback:
                    progress_callback(progress.to_dict())

                # 如果还有迭代次数，继续尝试
                if iteration < self.max_iterations:
                    time.sleep(1)  # 等待后重试
                    continue

                # 达到最大迭代次数仍未成功
                return {
                    "success": False,
                    "final_code": current_code,
                    "original_code": original_code,
                    "iterations": iteration,
                    "error": str(e),
                    "fix_history": self.fix_history,
                    "elapsed_time": time.time() - progress.start_time
                }

        # 达到最大迭代次数
        final_validation = self.validator.validate_algorithm_code(current_code, algorithm_name)
        return {
            "success": final_validation.is_valid,
            "final_code": current_code,
            "original_code": original_code,
            "iterations": self.max_iterations,
            "validation_result": asdict(final_validation),
            "fix_history": self.fix_history,
            "elapsed_time": time.time() - progress.start_time
        }

    def _generate_fix_prompt(self, code: str, validation_result: CodeValidationResult, iteration: int) -> str:
        """生成修复提示"""

        # 分类错误信息，优先处理关键错误
        critical_errors = []
        syntax_errors = []
        logic_errors = []
        structure_errors = []

        for error in validation_result.errors:
            error_msg = f"- {error.message}"
            if error.line_number:
                error_msg += f" (第 {error.line_number} 行)"
            if error.suggestion:
                error_msg += f"\n  建议修复: {error.suggestion}"

            if error.level.value == "critical":
                critical_errors.append(error_msg)
            elif "语法" in error.message or "syntax" in error.message.lower():
                syntax_errors.append(error_msg)
            elif "结构" in error.message or "缺失" in error.message:
                structure_errors.append(error_msg)
            else:
                logic_errors.append(error_msg)

        warning_messages = []
        for warning in validation_result.warnings:
            warning_msg = f"- {warning.message}"
            if warning.line_number:
                warning_msg += f" (第 {warning.line_number} 行)"
            if warning.suggestion:
                warning_msg += f"\n  建议修复: {warning.suggestion}"
            warning_messages.append(warning_msg)

        # 根据迭代次数调整修复策略
        strategy_description = self._get_strategy_description(iteration)

        prompt = f"""
你是一个专业的Python代码修复专家，专注于寻路算法开发。请分析以下代码并智能修复所有问题。

{strategy_description}

## 当前代码:
```python
{code}
```

## 错误分类与优先级:

### 🔥 严重错误 (必须修复):
{chr(10).join(critical_errors) if critical_errors else "无严重错误"}

### 🐛 语法错误 (必须修复):
{chr(10).join(syntax_errors) if syntax_errors else "无语法错误"}

### 🏗️ 结构错误 (必须修复):
{chr(10).join(structure_errors) if structure_errors else "无结构错误"}

### ⚠️ 逻辑错误 (需要修复):
{chr(10).join(logic_errors) if logic_errors else "无逻辑错误"}

### ⚡ 警告问题 (建议修复):
{chr(10).join(warning_messages) if warning_messages else "无警告"}

## 智能修复策略:

### 第一步: 理解算法意图
- 分析现有代码，理解其寻路策略
- 识别算法类型（BFS、DFS、A*、Dijkstra等）
- 确保不改变核心算法逻辑

### 第二步: 修复关键问题
1. **语法修复**: 修正Python语法错误
2. **结构完善**: 确保类和方法结构正确
3. **逻辑修复**: 修复算法逻辑缺陷
4. **规范优化**: 改进代码规范

### 第三步: 质量保证
- 确保 visited_order 正确记录
- 确保 find_path 返回正确的路径格式 [(y, x)]
- 确保 get_visited_order 返回访问顺序列表
- 添加必要的边界检查和异常处理

## 代码规范要求:
- ✅ 类名必须是: CustomPathfindingAlgorithm
- ✅ 必须包含方法: __init__(self, width, height)
- ✅ 必须包含方法: find_path(self, grid, start, end)
- ✅ 必须包含方法: get_visited_order(self)
- ✅ 必须包含属性: width, height, visited_order
- ✅ 坐标格式建议使用: (y, x)
- ✅ 添加类型注解和文档字符串（如果缺失）

## 输出要求:
请只返回修复后的完整Python代码，不要包含任何解释或其他文本。
如果代码已经正确，请直接返回原代码。
确保返回的代码可以直接执行，没有任何语法错误。
"""

        return prompt

    def _get_strategy_description(self, iteration: int) -> str:
        """根据迭代次数获取策略描述"""
        if iteration == 1:
            return """
### 💡 第1轮修复策略:
- 专注于修复语法错误和结构问题
- 确保基础的类和方法结构正确
- 快速解决阻塞性错误
"""
        elif iteration == 2:
            return """
### 🔄 第2轮修复策略:
- 深入修复逻辑错误
- 优化算法实现
- 验证方法的正确性
"""
        elif iteration == 3:
            return """
### ⚡ 第3轮修复策略:
- 精细化修复剩余问题
- 优化代码质量和可读性
- 增强代码健壮性
"""
        else:
            return """
### 🎯 最终修复策略:
- 专注于解决顽固问题
- 确保代码完全符合规范
- 验证所有功能的正确性
- 最大化代码质量评分
"""

    def _call_llm_for_fix(self, prompt: str) -> Optional[str]:
        """调用LLM进行代码修复"""
        api_key = self.llm_config.get_api_key(self.current_provider)
        if not api_key:
            raise ValueError("API key not configured")

        api_url = self.llm_config.get_api_url(self.current_provider)
        model = self.llm_config.get_model(self.current_provider)

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
            "max_tokens": 3000,
            "temperature": 0.3  # 降低温度以提高一致性
        }

        try:
            response = requests.post(api_url, headers=headers, json=data, timeout=60)
            if response.status_code == 200:
                result = response.json()
                code = result["choices"][0]["message"]["content"]
                return self._clean_generated_code(code)
            else:
                raise Exception(f"API call failed: {response.status_code} - {response.text}")
        except Exception as e:
            raise Exception(f"LLM call failed: {str(e)}")

    def _clean_generated_code(self, code: str) -> str:
        """清理生成的代码"""
        import re

        # 移除markdown代码块标记
        code = re.sub(r'```python\n?', '', code)
        code = re.sub(r'```\n?', '', code)

        # 移除多余的前后空白
        code = code.strip()

        # 移除空行（但保留必要的分隔）
        lines = code.split('\n')
        cleaned_lines = []
        for i, line in enumerate(lines):
            if line.strip() or (i < len(lines) - 1 and lines[i + 1].strip()):
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _optimize_code(self, code: str, progress_callback=None) -> str:
        """优化代码"""
        if progress_callback:
            progress_callback({
                "optimization_step": "start",
                "message": "开始代码优化..."
            })

        # 分析修复历史，制定优化策略
        optimization_strategy = self._analyze_optimization_strategy()

        # 使用LLM进行优化
        optimization_prompt = f"""
请对以下修复后的代码进行智能优化，保持其功能完全不变：

```python
{code}
```

## 优化策略:
{optimization_strategy}

## 具体优化要求:

### 1. 代码质量提升
- 添加完整的方法文档字符串，说明参数和返回值
- 为所有方法参数和返回值添加类型注解
- 改善代码结构和可读性
- 添加必要的注释解释关键算法步骤

### 2. 性能优化
- 优化数据结构使用
- 减少不必要的计算
- 改进循环和条件判断
- 使用更Pythonic的代码风格

### 3. 健壮性增强
- 添加适当的边界检查
- 增加异常处理机制
- 验证输入参数的有效性
- 确保算法在各种情况下都能安全运行

### 4. 规范化改进
- 确保变量命名符合Python规范
- 统一代码风格
- 移除冗余代码
- 确保代码格式一致性

## 输出要求:
只返回优化后的完整Python代码，不要包含任何解释或其他文本。
确保优化后的代码功能与原代码完全相同，但质量显著提升。
"""

        try:
            optimized_code = self._call_llm_for_fix(optimization_prompt)

            if progress_callback:
                progress_callback({
                    "optimization_step": "complete",
                    "message": "代码优化完成"
                })

            return optimized_code if optimized_code else code

        except Exception as e:
            if progress_callback:
                progress_callback({
                    "optimization_step": "error",
                    "message": f"优化失败，使用原代码: {str(e)}"
                })
            return code

    def _analyze_optimization_strategy(self) -> str:
        """分析修复历史，制定优化策略"""
        if not self.fix_history:
            return """
### 基础优化策略:
- 这是一个全新生成的算法
- 专注于基础代码质量提升
- 确保代码结构清晰和规范
"""

        latest_fix = self.fix_history[-1]
        total_iterations = len(self.fix_history)

        # 分析修复历史中的问题类型
        logic_issues_count = 0
        syntax_issues_count = 0
        structure_issues_count = 0

        for fix in self.fix_history:
            for error in fix["original_validation"]["errors"]:
                msg = error["message"].lower()
                if "语法" in msg or "syntax" in msg:
                    syntax_issues_count += 1
                elif "结构" in msg or "缺失" in msg:
                    structure_issues_count += 1
                else:
                    logic_issues_count += 1

        strategy = f"""
### 基于修复历史的优化策略:
- 经过 {total_iterations} 轮修复，已解决大部分基础问题
- 历史上存在语法问题 {syntax_issues_count} 个，结构问题 {structure_issues_count} 个，逻辑问题 {logic_issues_count} 个
"""

        if total_iterations >= 3:
            strategy += """
### 重点优化方向:
1. **深度优化**: 代码基础已稳定，可进行深度优化
2. **性能提升**: 优化算法执行效率
3. **可读性增强**: 提升代码的可维护性
4. **健壮性加固**: 增强错误处理能力
"""
        else:
            strategy += """
### 重点优化方向:
1. **基础巩固**: 确保代码结构稳定可靠
2. **规范化**: 统一代码风格和规范
3. **文档完善**: 添加必要的文档和注释
4. **安全检查**: 增加边界和异常处理
"""

        return strategy

    def _calculate_improvements(self, original: CodeValidationResult, new: CodeValidationResult) -> Dict[str, int]:
        """计算改进情况"""
        return {
            "errors_fixed": len(original.errors) - len(new.errors),
            "warnings_fixed": len(original.warnings) - len(new.warnings),
            "score_improvement": new.overall_score - original.overall_score
        }

    def get_fix_summary(self) -> Dict[str, Any]:
        """获取修复摘要"""
        if not self.fix_history:
            return {"message": "暂无修复历史"}

        total_iterations = len(self.fix_history)
        final_iteration = self.fix_history[-1]
        initial_validation = final_iteration["original_validation"]
        final_validation = final_iteration["new_validation"]

        return {
            "total_iterations": total_iterations,
            "initial_errors": len(initial_validation["errors"]),
            "final_errors": len(final_validation["errors"]),
            "initial_warnings": len(initial_validation["warnings"]),
            "final_warnings": len(final_validation["warnings"]),
            "initial_score": initial_validation["overall_score"],
            "final_score": final_validation["overall_score"],
            "success": final_validation["is_valid"],
            "fix_rate": self._calculate_fix_rate()
        }

    def _calculate_fix_rate(self) -> float:
        """计算修复成功率"""
        if not self.fix_history:
            return 0.0

        successful_fixes = 0
        for fix in self.fix_history:
            if fix["new_validation"]["is_valid"]:
                successful_fixes += 1
                break

        return 1.0 if successful_fixes > 0 else 0.0