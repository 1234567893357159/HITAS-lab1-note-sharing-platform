
# 消息中间件测试报告

## 1. 测试环境
- 操作系统: Windows
- Python版本: 3.12
- 测试时间: 2026-06-01 00:10:09

## 2. 测试结果汇总
- 总测试数: 8
- 通过数: 8
- 失败数: 0
- 通过率: 100.0%
- 总耗时: 63.42 秒

## 3. 详细测试结果

### 1. 连接测试
**状态**: [OK] 通过
**文件**: tests/test_connection.py

**测试详情**:

```
Test 1: Normal Connection
Test 2: Manual Disconnect
Test 3: Reconnect After Disconnect
Test 4: Multiple Queries
Test Results Summary
Pass rate: 4/4 (100.0%)
```

### 2. 消息路由测试
**状态**: [OK] 通过
**文件**: tests/test_routing.py

**测试详情**:

```
Test 1: Publish Note
Test 2: Like Note
Test 3: Comment Note
Test 4: Delete Note
Test Results Summary
[OK] Test 1: Publish Note: Passed
[OK] Test 2: Like Note: Passed
[OK] Test 3: Comment Note: Passed
[OK] Test 4: Delete Note: Passed
Pass rate: 4/4 (100.0%)
```

### 3. 查询功能测试
**状态**: [OK] 通过
**文件**: tests/test_query.py

**测试详情**:

```
Test 1: Get All Notes
Test 2: Get Single Note
Test 3: Get Comment List
Test 4: Get Like Count
Test 5: Unknown Query Type
Test Results Summary
[OK] Test 1: Get All Notes: Passed
[OK] Test 2: Get Single Note: Passed
[OK] Test 3: Get Comment List: Passed
[OK] Test 4: Get Like Count: Passed
[OK] Test 5: Unknown Query Type: Passed
Pass rate: 5/5 (100.0%)
```

### 4. 端到端测试
**状态**: [OK] 通过
**文件**: tests/test_e2e.py

**测试详情**:

```
Step 1: Publish Note
Step 2: Query Note List
Step 3: Like Note
Step 4: Verify Like Count
Step 5: Comment Note
Step 6: Verify Comment
Test Results Summary
Pass rate: 6/6 (100.0%)
```

### 5. 查询响应时间测试
**状态**: [OK] 通过
**文件**: tests/test_query_latency.py

**测试详情**:

```
Test Results
Query count: 100
Avg response time: 130.27 ms
Min response time: 100.21 ms
Max response time: 226.01 ms
P50 response time: 110.40 ms
P95 response time: 221.02 ms
P99 response time: 226.01 ms
```

### 6. 并发测试
**状态**: [OK] 通过
**文件**: tests/test_concurrency.py

**测试详情**:

```
Thread 9: Avg response time 122.43 ms
Thread 2: Avg response time 133.46 ms
Thread 0: Avg response time 134.53 ms
Thread 5: Avg response time 134.43 ms
Thread 8: Avg response time 154.16 ms
Thread 3: Avg response time 154.30 ms
Thread 1: Avg response time 155.09 ms
Thread 6: Avg response time 154.99 ms
Thread 4: Avg response time 155.09 ms
Thread 7: Avg response time 166.64 ms
Test Results
Thread count: 10
Total queries: 100
Total time: 1.67 seconds
System throughput: 59.82 queries/sec
Avg response time: 146.51 ms
Max response time: 166.64 ms
Min response time: 122.43 ms
```

### 7. 吞吐率测试
**状态**: [OK] 通过
**文件**: tests/test_throughput.py

**测试详情**:

```
Throughput Test - 1000 messages
Test Results
Messages sent: 1000
Total time: 0.05 seconds
Throughput: 21622.80 messages/sec
```

### 8. 压力测试
**状态**: [OK] 通过
**文件**: tests/test_stress.py

**测试详情**:

```
Test Results
Total messages: 2000
Total time: 0.53 seconds
Throughput: 3744.77 messages/sec
```

## 4. 性能指标总结

| 测试类型 | 指标 | 数值 |
|---------|------|------|
| 查询响应时间测试 | 平均响应时间 | 130.27 ms |
| 查询响应时间测试 | P95响应时间 | 221.02 ms |
| 并发测试 | 系统吞吐率 | 59.82 queries/sec |
| 并发测试 | 平均响应时间 | 146.51 ms |
| 吞吐率测试 | 吞吐率 | 21622.80 messages/sec |
| 吞吐率测试 | 平均延迟 | 0.05 ms |
| 压力测试 | 总消息数 | 2000 |
| 压力测试 | 吞吐率 | 3744.77 messages/sec |


## 5. 结论

系统功能完整，性能良好，满足实验要求。

**通过率**: 100.0%

**总体评价**: 优秀
