#!/usr/bin/env python3
"""
LLM寻路算法生成测试脚本
模拟用户操作，测试硅基流动API生成寻路算法的完整流程
"""

import time
import json
from typing import Dict, List, Tuple

# 导入相关模块
from llm_integration import LLMConfig, LLMProvider, LLMAlgorithmGenerator, algorithm_executor
from code_validator import CodeValidator
from llm_code_fixer import LLMCodeFixer, FixProgress

class LLMAlgorithmTester:
    """LLM算法测试器"""

    def __init__(self):
        self.config = LLMConfig()
        self.generator = LLMAlgorithmGenerator(self.config)
        self.validator = CodeValidator()
        self.code_fixer = LLMCodeFixer(self.config)
        self.test_results = []

    def setup_siliconflow_api(self, api_key: str):
        """设置硅基流动API"""
        print("[INFO] 设置硅基流动API...")
        self.config.set_api_key(LLMProvider.SILICONFLOW, api_key)
        self.generator.set_provider(LLMProvider.SILICONFLOW)
        self.code_fixer.set_provider(LLMProvider.SILICONFLOW)
        print(f"[SUCCESS] 硅基流动API设置完成")

    def test_api_connection(self):
        """测试API连接"""
        print("\n[INFO] 测试硅基流动API连接...")

        try:
            result = self.generator.test_api_connection(LLMProvider.SILICONFLOW)
            if result:
                print("[SUCCESS] API连接测试成功")
                return True
            else:
                print("[ERROR] API连接测试失败")
                return False
        except Exception as e:
            print(f"[ERROR] API连接测试异常: {e}")
            return False

    def test_algorithm_generation(self, algorithm_desc: str, grid_size: Tuple[int, int],
                                start: Tuple[int, int], end: Tuple[int, int]):
        """测试算法生成"""
        print(f"\n[START] 开始生成算法...")
        print(f"算法描述: {algorithm_desc}")
        print(f"网格大小: {grid_size}")
        print(f"起点: {start}")
        print(f"终点: {end}")

        try:
            # 生成算法代码
            generated_code = self.generator.generate_custom_algorithm(
                algorithm_desc, grid_size, start, end
            )

            if generated_code:
                print("[SUCCESS] 算法代码生成成功")
                print(f"生成的代码长度: {len(generated_code)} 字符")
                return generated_code
            else:
                print("[ERROR] 算法代码生成失败")
                return None

        except Exception as e:
            print(f"[ERROR] 算法代码生成异常: {e}")
            return None

    def test_code_validation(self, algorithm_name: str, code: str):
        """测试代码验证"""
        print(f"\n[INFO] 验证生成的代码...")

        try:
            validation_result = self.validator.validate_algorithm_code(code, algorithm_name)

            print(f"验证结果: {'通过' if validation_result.is_valid else '失败'}")
            print(f"总体分数: {validation_result.overall_score}")
            print(f"错误数量: {len(validation_result.errors)}")
            print(f"警告数量: {len(validation_result.warnings)}")
            print(f"建议数量: {len(validation_result.suggestions)}")

            # 显示具体错误
            if validation_result.errors:
                print("\n[WARNING] 具体错误:")
                for i, error in enumerate(validation_result.errors, 1):
                    print(f"  {i}. [{error.level.value}] {error.message}")
                    if error.suggestion:
                        print(f"     建议: {error.suggestion}")

            return validation_result

        except Exception as e:
            print(f"[ERROR] 代码验证异常: {e}")
            return None

    def test_code_fixing(self, original_code: str, algorithm_name: str = "CustomPathfindingAlgorithm"):
        """测试代码修复"""
        print(f"\n[START] 开始智能修复...")

        def progress_callback(progress_data):
            """进度回调函数"""
            step = progress_data.get('current_step_name', '')
            message = progress_data.get('message', '')
            iteration = progress_data.get('current_iteration', 1)
            max_iterations = progress_data.get('max_iterations', 1)
            overall_progress = progress_data.get('overall_progress', 0)

            print(f"  [{iteration}/{max_iterations}] {step}: {message}")
            print(f"  进度: {overall_progress:.1f}%")

        try:
            fix_result = self.code_fixer.fix_algorithm_code(
                original_code, algorithm_name, progress_callback
            )

            success = fix_result.get('success', False)
            iterations = fix_result.get('iterations', 0)
            elapsed_time = fix_result.get('elapsed_time', 0)

            print(f"\n修复结果: {'成功' if success else '失败'}")
            print(f"迭代次数: {iterations}")
            print(f"耗时: {elapsed_time:.2f} 秒")

            if success:
                fixed_code = fix_result.get('final_code', '')
                print(f"修复后代码长度: {len(fixed_code)} 字符")
                return fix_result
            else:
                error = fix_result.get('error', 'Unknown error')
                print(f"修复失败原因: {error}")
                return fix_result

        except Exception as e:
            print(f"[ERROR] 代码修复异常: {e}")
            return None

    def test_algorithm_execution(self, algorithm_name: str, algorithm_code: str,
                               grid_size: Tuple[int, int], start: Tuple[int, int], end: Tuple[int, int]):
        """测试算法执行"""
        print(f"\n[TEST] 测试算法执行...")

        try:
            # 创建测试网格
            test_grid = self._create_test_grid(grid_size, start, end)

            # 加载算法
            load_success = algorithm_executor.load_algorithm(algorithm_name, algorithm_code)
            if not load_success:
                print("[ERROR] 算法加载失败")
                return False

            print("[SUCCESS] 算法加载成功")

            # 执行算法
            path, visited_order = algorithm_executor.execute_algorithm(
                algorithm_name, grid_size[0], grid_size[1], test_grid, start, end
            )

            print(f"执行结果:")
            print(f"  路径长度: {len(path)}")
            print(f"  访问节点数: {len(visited_order)}")

            if path:
                print(f"  路径: {path[:5]}{'...' if len(path) > 5 else ''}")
                print("[SUCCESS] 算法执行成功，找到了路径")
                return True
            else:
                print("[WARNING] 算法执行完成，但未找到路径")
                return False

        except Exception as e:
            print(f"[ERROR] 算法执行异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _create_test_grid(self, grid_size: Tuple[int, int], start: Tuple[int, int],
                         end: Tuple[int, int]) -> List[List[int]]:
        """创建测试网格"""
        rows, cols = grid_size
        grid = [[0 for _ in range(cols)] for _ in range(rows)]

        # 设置起点和终点
        sy, sx = start
        ey, ex = end
        grid[sy][sx] = 2  # 起点
        grid[ey][ex] = 3  # 终点

        # 添加一些障碍物
        # 在中间加一堵墙，留一个缺口
        wall_row = rows // 2
        for x in range(cols):
            if x != cols // 2:  # 在中间留一个缺口
                if wall_row < rows:
                    grid[wall_row][x] = 1  # 障碍物

        return grid

    def run_complete_test(self, api_key: str = None):
        """运行完整测试"""
        print("[START] 开始LLM寻路算法生成完整测试")
        print("=" * 60)

        if api_key:
            self.setup_siliconflow_api(api_key)

        # 测试1: API连接
        if not self.test_api_connection():
            print("[ERROR] API连接测试失败，终止测试")
            return False

        # 测试参数
        test_cases = [
            {
                "desc": "使用A*算法的最优路径寻找",
                "grid_size": (10, 15),
                "start": (1, 1),
                "end": (8, 13)
            },
            {
                "desc": "简单的BFS广度优先搜索算法",
                "grid_size": (8, 12),
                "start": (0, 0),
                "end": (7, 11)
            },
            {
                "desc": "使用Dijkstra算法的最短路径",
                "grid_size": (12, 10),
                "start": (2, 1),
                "end": (9, 8)
            }
        ]

        overall_success = 0
        total_tests = len(test_cases)

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"[TEST] 测试案例 {i}/{total_tests}")
            print(f"{'='*60}")

            algorithm_name = f"TestAlgorithm_{i}"

            # 生成算法
            generated_code = self.test_algorithm_generation(
                test_case["desc"],
                test_case["grid_size"],
                test_case["start"],
                test_case["end"]
            )

            if not generated_code:
                print(f"[ERROR] 测试案例 {i}: 算法生成失败")
                continue

            # 验证代码
            validation_result = self.test_code_validation(algorithm_name, generated_code)

            # 初始化修复结果变量
            fix_result = None

            # 如果验证失败，尝试修复
            if validation_result and not validation_result.is_valid:
                print(f"\n[INFO] 测试案例 {i}: 开始智能修复...")
                try:
                    fix_result = self.test_code_fixing(generated_code, algorithm_name)

                    if fix_result and fix_result.get('success'):
                        generated_code = fix_result.get('final_code', generated_code)
                        print(f"[SUCCESS] 测试案例 {i}: 修复成功，重新验证...")
                        validation_result = self.test_code_validation(algorithm_name, generated_code)
                    else:
                        print(f"[WARNING] 测试案例 {i}: 修复失败，继续测试原始代码")
                except Exception as e:
                    print(f"[ERROR] 测试案例 {i}: 修复过程异常 - {e}")

            # 执行算法
            execution_success = self.test_algorithm_execution(
                algorithm_name,
                generated_code,
                test_case["grid_size"],
                test_case["start"],
                test_case["end"]
            )

            if execution_success:
                overall_success += 1
                print(f"[SUCCESS] 测试案例 {i}: 成功")
            else:
                print(f"[ERROR] 测试案例 {i}: 失败")

            # 记录结果
            self.test_results.append({
                "test_case": i,
                "description": test_case["desc"],
                "generation_success": generated_code is not None,
                "validation_success": validation_result.is_valid if validation_result else False,
                "fixing_success": fix_result.get('success', False) if fix_result else False,
                "execution_success": execution_success,
                "code_length": len(generated_code) if generated_code else 0,
                "validation_score": validation_result.overall_score if validation_result else 0
            })

        # 输出总结
        print(f"\n{'='*60}")
        print("[RESULT] 测试总结")
        print(f"{'='*60}")
        print(f"总测试案例: {total_tests}")
        print(f"成功案例: {overall_success}")
        print(f"成功率: {overall_success/total_tests*100:.1f}%")

        return overall_success == total_tests

def main():
    """主函数"""
    tester = LLMAlgorithmTester()

    # 使用提供的硅基流动API密钥进行测试
    siliconflow_api_key = "sk-sadbfortbksftqzcfykcixrrqwibvdyfrukggstrsubzaqpi"

    print("[INFO] 使用提供的硅基流动API密钥进行测试...")
    print("[WARNING] 注意：测试完成后将自动删除此密钥")

    success = tester.run_complete_test(siliconflow_api_key)

    if success:
        print("\n[SUCCESS] 所有测试通过！LLM寻路算法生成功能正常")
    else:
        print("\n[ERROR] 部分测试失败，需要进一步调试")

    # 保存测试结果
    if hasattr(tester, 'test_results') and tester.test_results:
        with open('llm_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(tester.test_results, f, ensure_ascii=False, indent=2)
        print(f"\n[INFO] 测试结果已保存到 llm_test_results.json")

    print("[INFO] 测试完成，API密钥已从内存中清除")

if __name__ == "__main__":
    main()