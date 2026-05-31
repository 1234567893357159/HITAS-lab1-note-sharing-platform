# 测试文档

## 测试脚本说明

本目录包含消息中间件的完整测试套件。

### 测试列表

| 测试脚本 | 说明 | 类别 |
|----------|------|------|
| `test_routing.py` | 测试消息路由功能 | 功能测试 |
| `test_query.py` | 测试查询功能 | 功能测试 |
| `test_throughput.py` | 测试消息吞吐率 | 性能测试 |
| `test_query_latency.py` | 测试查询响应时间 | 性能测试 |
| `test_concurrency.py` | 测试并发性能 | 性能测试 |
| `test_e2e.py` | 端到端业务流程测试 | 集成测试 |
| `test_stress.py` | 压力测试 | 压力测试 |
| `test_connection.py` | 测试连接管理 | 异常测试 |
| `test_invalid_message.py` | 测试无效消息处理 | 异常测试 |
| `run_all_tests.py` | 运行所有测试并生成报告 | 自动化测试 |

## 使用方法

### 前置条件

1. 确保中间件服务正在运行：
```bash
cd f:\学习资料\软件架构与中间件\lab1\note-sharing-platform
python run.py
```

2. 等待服务完全启动（约5秒）

### 运行单个测试

```bash
# 运行消息路由测试
python tests/test_routing.py

# 运行查询功能测试
python tests/test_query.py

# 运行吞吐率测试
python tests/test_throughput.py

# 运行查询响应时间测试
python tests/test_query_latency.py

# 运行并发测试
python tests/test_concurrency.py

# 运行端到端测试
python tests/test_e2e.py

# 运行压力测试
python tests/test_stress.py

# 运行连接测试
python tests/test_connection.py

# 运行无效消息测试
python tests/test_invalid_message.py
```

### 运行所有测试

```bash
# 一键运行所有测试并生成报告
python tests/run_all_tests.py
```

测试完成后，会在当前目录生成 `test_report.md` 文件。

## 测试报告示例

```markdown
# 消息中间件测试报告

## 1. 测试环境
- 操作系统: Windows
- Python版本: 3.12
- 测试时间: 2026-05-31 23:00:00

## 2. 测试结果汇总
- 总测试数: 9
- 通过数: 9
- 失败数: 0
- 通过率: 100.0%
- 总耗时: 45.23 秒

## 3. 详细测试结果

### 1. 消息路由测试
**状态**: ✅ 通过
**文件**: test_routing.py

### 2. 查询功能测试
**状态**: ✅ 通过
**文件**: test_query.py

...

## 4. 结论

系统功能完整，性能良好，满足实验要求。

**通过率**: 100.0%

**总体评价**: 优秀
```

## 测试参数调整

### 吞吐率测试

修改 `test_throughput.py` 中的参数：

```python
# 默认发送 1000 条消息
result = test_throughput(1000)

# 可以修改为其他数量
result = test_throughput(500)  # 发送 500 条
result = test_throughput(2000)  # 发送 2000 条
```

### 查询响应时间测试

修改 `test_query_latency.py` 中的参数：

```python
# 默认执行 100 次查询
result = test_query_latency(100)

# 可以修改为其他次数
result = test_query_latency(50)   # 执行 50 次
result = test_query_latency(200)  # 执行 200 次
```

### 并发测试

修改 `test_concurrency.py` 中的参数：

```python
# 默认 10 个线程，每个线程 10 次查询
result = test_concurrency(10, 10)

# 可以修改为其他配置
result = test_concurrency(20, 10)  # 20 个线程
result = test_concurrency(10, 20)  # 每线程 20 次查询
```

### 压力测试

修改 `test_stress.py` 中的参数：

```python
# 默认 20 个线程，每个线程 100 条消息
result = test_stress(20, 100)

# 可以修改为其他配置
result = test_stress(50, 100)  # 50 个线程
result = test_stress(20, 200)  # 每线程 200 条消息
```

## 注意事项

1. **服务必须先启动**：所有测试都需要中间件服务正在运行
2. **测试间隔**：连续运行多个测试时，建议间隔1秒以上
3. **压力测试**：压力测试会发送大量消息，建议在单独的环境中进行
4. **数据库清理**：如需重置测试环境，可以删除 `data/notes.db` 文件

## 性能指标参考

| 指标 | 优秀 | 良好 | 需改进 |
|------|------|------|--------|
| 消息吞吐率 | >1000 条/秒 | 500-1000 条/秒 | <500 条/秒 |
| 查询平均响应时间 | <20 ms | 20-50 ms | >50 ms |
| 并发吞吐率 | >80 查询/秒 | 50-80 查询/秒 | <50 查询/秒 |

## 故障排查

### 测试失败：连接被拒绝

**原因**：中间件服务未启动

**解决**：
```bash
python run.py
```

### 测试失败：查询超时

**原因**：中间件负载过高或网络问题

**解决**：
1. 检查中间件日志
2. 减少并发数
3. 增加超时时间

### 测试失败：数据库错误

**原因**：数据库文件损坏或不存在

**解决**：
```bash
# 删除数据库文件，系统会自动创建新的
rm data/notes.db
```