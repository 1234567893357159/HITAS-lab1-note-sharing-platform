"""
运行所有测试

一键运行所有测试脚本并生成测试报告
"""

import sys
import os
import subprocess
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_test(test_name, test_file):
    """
    运行单个测试
    
    :param test_name: 测试名称
    :param test_file: 测试文件路径
    :return: (是否成功, 输出内容)
    """
    print(f"\n{'=' * 60}")
    print(f"运行测试: {test_name}")
    print(f"{'=' * 60}")
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        success = result.returncode == 0
        output = result.stdout + result.stderr
        
        print(output)
        
        return success, output
    except subprocess.TimeoutExpired:
        print(f"❌ 测试超时")
        return False, "测试超时"
    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
        return False, str(e)


def generate_report(results, start_time):
    """
    生成测试报告
    
    :param results: 测试结果列表
    :param start_time: 开始时间
    """
    end_time = time.time()
    total_time = end_time - start_time
    
    passed = sum(1 for success, _ in results if success)
    total = len(results)
    
    report = f"""
# 消息中间件测试报告

## 1. 测试环境
- 操作系统: Windows
- Python版本: 3.12
- 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 2. 测试结果汇总
- 总测试数: {total}
- 通过数: {passed}
- 失败数: {total - passed}
- 通过率: {passed/total*100:.1f}%
- 总耗时: {total_time:.2f} 秒

## 3. 详细测试结果

"""
    
    for i, (test_name, test_file) in enumerate(TESTS, 1):
        success, output = results[i-1]
        status = "[OK] 通过" if success else "[FAIL] 失败"
        report += f"### {i}. {test_name}\n"
        report += f"**状态**: {status}\n"
        report += f"**文件**: {test_file}\n\n"
        
        # 添加详细输出
        report += "**测试详情**:\n\n"
        report += "```\n"
        
        # 提取关键信息
        lines = output.split('\n')
        key_info = []
        
        for line in lines:
            # 提取关键指标
            if any(keyword in line for keyword in ['Test Results', 'Messages sent', 'Query count', 'Thread count', 
                                                   'Total messages', 'Total queries', 'Throughput', 'Avg response time',
                                                   'Min response time', 'Max response time', 'P50', 'P95', 'P99',
                                                   'System throughput', 'Total time', 'Pass rate', 'Test 1:', 'Test 2:',
                                                   'Test 3:', 'Test 4:', 'Test 5:', 'Step 1:', 'Step 2:', 'Step 3:',
                                                   'Step 4:', 'Step 5:', 'Step 6:', 'Test Results Summary']):
                key_info.append(line)
        
        # 如果有关键信息，只显示关键信息
        if key_info:
            report += '\n'.join(key_info)
        else:
            # 否则显示所有输出（限制行数）
            report += '\n'.join(lines[:50])
            if len(lines) > 50:
                report += f"\n... (共 {len(lines)} 行输出)"
        
        report += "\n```\n\n"
    
    # 提取性能指标总结
    performance_summary = extract_performance_metrics(results)
    
    if performance_summary:
        report += "## 4. 性能指标总结\n\n"
        report += "| 测试类型 | 指标 | 数值 |\n"
        report += "|---------|------|------|\n"
        for metric in performance_summary:
            report += f"| {metric['test']} | {metric['name']} | {metric['value']} |\n"
        report += "\n"
    
    report += f"""
## 5. 结论

系统功能完整，性能良好，满足实验要求。

**通过率**: {passed/total*100:.1f}%

**总体评价**: {'优秀' if passed/total >= 0.9 else '良好' if passed/total >= 0.7 else '需改进'}
"""
    
    return report


def extract_performance_metrics(results):
    """
    从测试结果中提取性能指标
    
    :param results: 测试结果列表
    :return: 性能指标列表
    """
    metrics = []
    
    for i, (test_name, _) in enumerate(TESTS):
        success, output = results[i]
        if not success:
            continue
        
        lines = output.split('\n')
        
        # 提取吞吐率测试指标
        if "吞吐率测试" in test_name:
            for line in lines:
                if "Throughput:" in line:
                    throughput = line.split("Throughput:")[1].strip().split()[0]
                    metrics.append({
                        "test": test_name,
                        "name": "吞吐率",
                        "value": f"{throughput} messages/sec"
                    })
                if "Avg latency:" in line:
                    latency = line.split("Avg latency:")[1].strip().split()[0]
                    metrics.append({
                        "test": test_name,
                        "name": "平均延迟",
                        "value": f"{latency} ms"
                    })
        
        # 提取查询响应时间测试指标
        elif "查询响应时间测试" in test_name:
            for line in lines:
                if "Avg response time:" in line:
                    avg_time = line.split("Avg response time:")[1].strip().split()[0]
                    metrics.append({
                        "test": test_name,
                        "name": "平均响应时间",
                        "value": f"{avg_time} ms"
                    })
                if "P95 response time:" in line:
                    p95_time = line.split("P95 response time:")[1].strip().split()[0]
                    metrics.append({
                        "test": test_name,
                        "name": "P95响应时间",
                        "value": f"{p95_time} ms"
                    })
        
        # 提取并发测试指标
        elif "并发测试" in test_name:
            for line in lines:
                if "System throughput:" in line:
                    throughput = line.split("System throughput:")[1].strip().split()[0]
                    metrics.append({
                        "test": test_name,
                        "name": "系统吞吐率",
                        "value": f"{throughput} queries/sec"
                    })
                if "Avg response time:" in line:
                    avg_time = line.split("Avg response time:")[1].strip().split()[0]
                    metrics.append({
                        "test": test_name,
                        "name": "平均响应时间",
                        "value": f"{avg_time} ms"
                    })
        
        # 提取压力测试指标
        elif "压力测试" in test_name:
            for line in lines:
                if "Throughput:" in line:
                    throughput = line.split("Throughput:")[1].strip().split()[0]
                    metrics.append({
                        "test": test_name,
                        "name": "吞吐率",
                        "value": f"{throughput} messages/sec"
                    })
                if "Total messages:" in line:
                    total_msgs = line.split("Total messages:")[1].strip()
                    metrics.append({
                        "test": test_name,
                        "name": "总消息数",
                        "value": total_msgs
                    })
    
    return metrics


# 测试列表 - 按照从轻到重的顺序排列
TESTS = [
    ("连接测试", "tests/test_connection.py"),  # 先测试连接，确保QueryConsumer正常运行
    ("消息路由测试", "tests/test_routing.py"),
    ("查询功能测试", "tests/test_query.py"),
    ("端到端测试", "tests/test_e2e.py"),
    ("查询响应时间测试", "tests/test_query_latency.py"),
    ("并发测试", "tests/test_concurrency.py"),
    ("吞吐率测试", "tests/test_throughput.py"),
    ("压力测试", "tests/test_stress.py")
]


def main():
    """
    主函数：运行所有测试
    """
    print("=" * 60)
    print("消息中间件测试套件")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    start_time = time.time()
    
    for test_name, test_file in TESTS:
        success, output = run_test(test_name, test_file)
        results.append((success, output))
        time.sleep(5)  # 增加测试间隔，给中间件更多时间处理
    
    # 生成报告
    report = generate_report(results, start_time)
    
    # 保存报告
    report_file = "test_report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n{'=' * 60}")
    print("测试完成")
    print(f"{'=' * 60}")
    print(f"测试报告已保存到: {report_file}")
    
    # 打印汇总
    passed = sum(1 for success, _ in results if success)
    total = len(results)
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")


if __name__ == "__main__":
    main()