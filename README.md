# 笔记分享平台

## 项目概述

本项目是一个基于**事件驱动架构（EDA）**的笔记分享平台，核心特点是通过**自定义消息中间件**实现完全解耦和异步事件处理。

**核心设计理念**：
- **Flask 不直接访问数据库**：所有数据库操作都通过中间件进行
- **生产者-消费者模式**：实现组件间的异步通信
- **发布-订阅模式**：支持多消费者订阅同一主题

---

## 一、软件架构设计

### 1.1 架构风格：事件驱动架构（EDA）

事件驱动架构是一种基于事件产生、检测、消费和响应的架构模式。本项目中：

| 角色 | 职责 | 实现组件 |
|------|------|----------|
| **事件生产者** | 发布事件到中间件 | Flask + MessageProducer |
| **事件代理** | 路由和分发事件 | MiddlewareServer |
| **事件消费者** | 处理事件并执行业务逻辑 | AuditConsumer, NoticeConsumer, StatConsumer, QueryConsumer |

### 1.2 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           整体架构（最终版）                                 │
└─────────────────────────────────────────────────────────────────────────────┘

                           ┌──────────────────┐
                           │   前端浏览器      │
                           │   (HTML/CSS)     │
                           │  - 表单提交       │
                           │  - 页面渲染       │
                           └───────┬──────────┘
                                   │ HTTP POST/GET
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Flask Web 应用                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         路由层                                      │   │
│  │  GET  /                  → index()                                 │   │
│  │  GET  /note/<note_id>    → note_detail()                           │   │
│  │  GET  /add               → add_note() [展示表单]                    │   │
│  │  POST /add               → add_note() [处理提交]                    │   │
│  │  POST /note/<id>/like    → like_note()                             │   │
│  │  POST /note/<id>/comment → comment_note()                          │   │
│  │  POST /note/<id>/delete  → delete_note_route()                     │   │
│  └─────────────────────────┬───────────────────────────────────────────┘   │
│                            │                                              │
│        ┌───────────────────┴───────────────────┐                         │
│        ▼                                       ▼                         │
│  ┌──────────────┐                     ┌──────────────────┐                │
│  │ QueryClient  │                     │ MessageProducer  │                │
│  │  (Python)    │                     │   (Python)       │                │
│  └──────┬───────┘                     └────────┬─────────┘                │
└─────────┼──────────────────────────────────────┼───────────────────────────┘
          │ query/request                        │ note/*
          ▼                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          消息中间件 (MiddlewareServer)                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    TopicRouter (主题路由)                           │   │
│  │  query/request → QueryConsumer                                     │   │
│  │  note/publish  → AuditConsumer                                     │   │
│  │  note/like     → NoticeConsumer + StatConsumer                     │   │
│  │  note/comment  → NoticeConsumer + StatConsumer                     │   │
│  │  note/delete   → QueryConsumer                                     │   │
│  │  query/response → 回传给 QueryClient                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
          │                                      │
          ▼                                      ▼
┌──────────────────────────────┐     ┌──────────────────────────────────────┐
│        QueryConsumer         │     │   AuditConsumer + NoticeConsumer      │
│  - get_notes                │     │   + StatConsumer                     │
│  - get_note                 │     │                                      │
│  - get_comments             │     │  AuditConsumer:                      │
│  - get_like_count           │     │    - 处理 note/publish               │
│  - delete_note              │     │    - 保存笔记到数据库                │
│                             │     │                                      │
│  查询数据库并返回结果        │     │  NoticeConsumer:                     │
│                             │     │    - 处理 note/like                  │
│                             │     │    - 处理 note/comment               │
│                             │     │    - 更新点赞/评论计数               │
│                             │     │                                      │
│                             │     │  StatConsumer:                       │
│                             │     │    - 统计热度数据                    │
└──────────────────────────────┘     └──────────────────────────────────────┘
          │                                      │
          └──────────────────────────────────────┘
                             │
                             ▼
                   ┌─────────────────┐
                   │   SQLite 数据库  │
                   │  notes/comments │
                   │  /likes/logs    │
                   └─────────────────┘
```

### 1.3 组件职责详解

| 组件 | 层级 | 职责 | 是否访问数据库 |
|------|------|------|---------------|
| **Flask Web 服务器** | 表示层 | 处理 HTTP 请求、渲染 HTML 模板 | ❌ 否 |
| **MessageProducer** | 业务层 | 向中间件发布事件消息 | ❌ 否 |
| **QueryClient** | 业务层 | 通过中间件发送查询请求并接收响应 | ❌ 否 |
| **MiddlewareServer** | 中间件层 | 消息路由、队列管理、连接管理 | ❌ 否 |
| **AuditConsumer** | 数据层 | 审核并保存新发布的笔记 | ✅ 是 |
| **NoticeConsumer** | 数据层 | 处理点赞、评论事件 | ✅ 是 |
| **StatConsumer** | 数据层 | 更新笔记热度分数 | ✅ 是 |
| **QueryConsumer** | 数据层 | 处理数据库查询请求和删除事件 | ✅ 是 |
| **SQLite 数据库** | 存储层 | 持久化所有数据 | - |

---

## 二、中间件设计

### 2.1 核心组件

#### 2.1.1 中间件服务器（MiddlewareServer）

```python
# 核心职责：
1. TCP Socket 监听（端口 5001）
2. 接收客户端连接（生产者、消费者、查询客户端）
3. 解析消息类型并路由
4. 管理消息队列和查询队列
5. 维护主题订阅关系
```

**消息处理逻辑**：

| 消息类型 | 处理方式 | 目标队列 |
|----------|----------|----------|
| `query` | 查询请求 | query_queue |
| `subscribe` | 订阅注册 | TopicRouter |
| `publish` | 事件发布 | msg_queue |

#### 2.1.2 消息类（Message）

```python
# 数据结构
{
    "topic": "note/publish",      # 消息主题
    "content": {...},             # 消息内容
    "timestamp": "2024-01-01T12:00:00",  # 创建时间
    "message_id": "uuid-xxx"      # 唯一标识
}

# 核心方法
- to_json(): 序列化为 JSON 字符串
- from_json(): 从 JSON 反序列化
```

#### 2.1.3 消息队列（MessageQueue）

```python
# 设计特点
- 线程安全：使用 threading.Lock 保证并发安全
- FIFO 顺序：先进先出处理消息
- 阻塞获取：队列为空时阻塞等待

# 核心方法
- put_message(message): 入队（线程安全）
- get_message(): 出队（线程安全，阻塞）
- is_empty(): 检查队列是否为空
```

#### 2.1.4 主题路由（TopicRouter）

```python
# 核心数据结构
subscribers = {
    "note/publish": [socket1, socket2],
    "note/like": [socket3],
    "query/request": [socket4]
}

# 核心方法
- subscribe(topic, socket): 订阅主题
- unsubscribe(topic, socket): 取消订阅
- get_subscribers(topic): 获取主题订阅者列表
```

### 2.2 消息分发机制

#### 2.2.1 分发流程

```
消息入队 → 分发线程轮询 → 获取订阅者列表 → 广播消息
     │           │                  │              │
     ▼           ▼                  ▼              ▼
 msg_queue  dispatch_messages()  get_subscribers()  sendall()
```

#### 2.2.2 双队列设计

| 队列 | 用途 | 分发线程 |
|------|------|----------|
| `msg_queue` | 处理事件消息（发布、点赞、评论、删除） | `dispatch_messages` |
| `query_queue` | 处理查询请求 | `dispatch_queries` |

**设计原因**：
- 查询请求需要更高的响应优先级
- 分离事件处理和查询处理，避免相互阻塞
- 便于独立调整处理策略

### 2.3 支持的消息主题

| 主题 | 生产者 | 消费者 | 消息结构 |
|------|--------|--------|----------|
| `note/publish` | Flask | AuditConsumer | `{note_id, title, content, author, created_at}` |
| `note/like` | Flask | NoticeConsumer, StatConsumer | `{note_id, user_id}` |
| `note/comment` | Flask | NoticeConsumer, StatConsumer | `{note_id, user_id, comment_text}` |
| `note/delete` | Flask | QueryConsumer | `{note_id}` |
| `query/request` | QueryClient | QueryConsumer | `{query_id, query_type, params}` |
| `query/response` | QueryConsumer | QueryClient | `{query_id, status, data}` |

---

## 三、消费者设计

### 3.1 消费者基类（MessageConsumer）

```python
# 通用功能
- connect(): 建立与中间件的 TCP 连接
- subscribe_topic(topic): 订阅指定主题
- start_listening(): 启动消息监听线程
- receive_message(): 接收并解析消息（处理 TCP 粘包）
- process_message(message): 处理消息（子类实现）
```

### 3.2 各消费者职责

#### AuditConsumer（审核消费者）
- **订阅主题**: `note/publish`
- **职责**:
  1. 接收笔记发布消息
  2. 验证笔记内容
  3. 保存到 `notes` 表
  4. 记录发布日志到 `publish_logs` 表

#### NoticeConsumer（通知消费者）
- **订阅主题**: `note/like`, `note/comment`
- **职责**:
  1. **点赞**: 调用 `add_like()` + 更新笔记点赞数
  2. **评论**: 调用 `add_comment()` + 更新笔记评论数

#### StatConsumer（统计消费者）
- **订阅主题**: `note/like`, `note/comment`
- **职责**:
  1. **点赞**: 热度 +2
  2. **评论**: 热度 +3

#### QueryConsumer（查询消费者）
- **订阅主题**: `query/request`, `note/delete`
- **支持查询类型**:
  | 查询类型 | 功能 | 参数 |
  |----------|------|------|
  | `get_notes` | 获取所有笔记 | 无 |
  | `get_note` | 获取单条笔记 | `{note_id}` |
  | `get_comments` | 获取评论列表 | `{note_id}` |
  | `get_like_count` | 获取点赞数 | `{note_id}` |

---

## 四、事件时序图

### 4.1 获取笔记列表（首页加载）

```
浏览器                          Flask                QueryClient           中间件            QueryConsumer          数据库
  │                              │                       │                   │                   │                    │
  │-- GET / --------------------▶│                       │                   │                   │                    │
  │                              │-- query("get_notes")▶│                   │                   │                    │
  │                              │                       │-- TCP发送请求----▶│                   │                    │
  │                              │                       │                   │-- 转发请求-------▶│                    │
  │                              │                       │                   │                   │-- SELECT * FROM notes
  │                              │                       │                   │                   │                    │
  │                              │                       │                   │                   │◀-- 返回结果         │
  │                              │                       │                   │◀-- 返回响应-------│                    │
  │                              │                       │◀-- TCP接收响应---│                   │                    │
  │                              │◀-- 返回结果-----------│                   │                   │                    │
  │◀-- HTML页面(渲染笔记列表)----│                       │                   │                   │                    │
```

### 4.2 添加笔记（表单提交）

```
浏览器                          Flask               MessageProducer       中间件            AuditConsumer         数据库
  │                              │                      │                   │                   │                    │
  │-- POST /add ----------------▶│                      │                   │                   │                    │
  │  {title, content, author}    │                      │                   │                   │                    │
  │                              │-- send_message("note/publish", data)▶│     │                   │                    │
  │                              │                      │-- TCP发送消息----▶│                   │                    │
  │                              │                      │                   │-- 路由到主题-----▶│                    │
  │                              │◀-- 返回成功------------│                   │                   │                    │
  │◀-- 重定向到首页--------------│                      │                   │                   │                    │
  │                              │                      │                   │                   │-- INSERT INTO notes
  │                              │                      │                   │                   │-- INSERT INTO publish_logs
```

### 4.3 点赞笔记（表单提交）

```
浏览器                          Flask               MessageProducer       中间件          NoticeConsumer      StatConsumer      数据库
  │                              │                      │                   │                   │                   │                    │
  │-- POST /note/id/like -------▶│                      │                   │                   │                   │                    │
  │                              │-- send_message("note/like", data)▶│       │                   │                   │                    │
  │                              │                      │-- TCP发送消息----▶│                   │                   │                    │
  │                              │◀-- 返回成功------------│                   │                   │                   │                    │
  │◀-- 重定向到笔记详情----------│                      │                   │                   │                   │                    │
  │                              │                      │                   │-- 同时路由到----▶│                   │                    │
  │                              │                      │                   │                   │-- INSERT INTO likes│                    │
  │                              │                      │                   │                   │-- UPDATE notes.likes│                    │
  │                              │                      │                   │                   │                   │-- 更新热度统计      │
```

### 4.4 评论笔记（表单提交）

```
浏览器                          Flask               MessageProducer       中间件          NoticeConsumer      StatConsumer      数据库
  │                              │                      │                   │                   │                   │                    │
  │-- POST /note/id/comment ----▶│                      │                   │                   │                   │                    │
  │  {user_id, comment_text}     │                      │                   │                   │                   │                    │
  │                              │-- send_message("note/comment", data)▶│     │                   │                   │                    │
  │                              │                      │-- TCP发送消息----▶│                   │                   │                    │
  │                              │◀-- 返回成功------------│                   │                   │                   │                    │
  │◀-- 重定向到笔记详情----------│                      │                   │                   │                   │                    │
  │                              │                      │                   │-- 同时路由到----▶│                   │                    │
  │                              │                      │                   │                   │-- INSERT INTO comments│                   │
  │                              │                      │                   │                   │-- UPDATE notes.comments│                   │
  │                              │                      │                   │                   │                   │-- 更新热度统计      │
```

### 4.5 删除笔记（表单提交）

```
浏览器                          Flask               MessageProducer       中间件            QueryConsumer          数据库
  │                              │                      │                   │                   │                    │
  │-- POST /note/id/delete -----▶│                      │                   │                   │                    │
  │                              │-- send_message("note/delete", data)▶│     │                   │                    │
  │                              │                      │-- TCP发送消息----▶│                   │                    │
  │                              │                      │                   │-- 路由到主题-----▶│                    │
  │                              │                      │                   │                   │-- DELETE FROM comments
  │                              │                      │                   │                   │-- DELETE FROM likes
  │                              │                      │                   │                   │-- DELETE FROM notes
  │                              │◀-- 等待0.1秒----------│                   │                   │                    │
  │◀-- 重定向到首页--------------│                      │                   │                   │                    │
```

---

## 五、查询流程（异步请求-响应模式）

### 5.1 流程图

```
用户请求笔记列表
       │
       ▼
Flask 调用 query_client.query("get_notes")
       │
       ▼
QueryClient 发送 {"type": "query", "query_id": "xxx", "query_type": "get_notes"}
       │
       ▼
MiddlewareServer 接收 → 放入 query_queue
       │
       ▼
dispatch_queries 线程分发 → QueryConsumer
       │
       ▼
QueryConsumer.execute_query() → 查询数据库
       │
       ▼
QueryConsumer 通过 MessageProducer 发布 "query/response"
       │
       ▼
MiddlewareServer 路由到订阅了 "query/response" 的 QueryClient
       │
       ▼
QueryClient 匹配 query_id → 返回结果给 Flask
       │
       ▼
Flask 渲染模板 → 返回 HTML 给浏览器
```

### 5.2 查询响应匹配机制

```python
# QueryClient 使用 query_id 匹配响应
pending_queries = {
    "1779782489.912358": None,  # 等待响应
    "1779782490.123456": {"status": "success", "data": [...]}  # 已收到
}
```

**超时处理**: 查询请求超时时间为 10 秒，超时后返回错误响应。

---

## 六、项目结构

```
note-sharing-platform/
├── middleware/                    # 消息中间件核心
│   ├── middleware_server.py       # 主服务器（TCP监听、消息路由）
│   ├── message.py                 # 消息数据结构（序列化/反序列化）
│   ├── message_queue.py           # 线程安全队列（双队列设计）
│   └── topic_router.py            # 主题订阅管理（发布-订阅模式）
├── producer/                      # 消息生产者
│   ├── producer.py                # 事件消息生产者（发布事件）
│   └── query_client.py            # 查询客户端（请求-响应模式）
├── consumers/                     # 后台消费者（唯一访问数据库）
│   ├── base_consumer.py           # 消费者基类（连接、订阅、监听）
│   ├── audit_consumer.py          # 审核处理器（笔记发布）
│   ├── notice_consumer.py         # 通知处理器（点赞、评论）
│   ├── stat_consumer.py           # 统计处理器（热度更新）
│   └── query_consumer.py          # 查询处理器（数据库查询、删除）
├── web/                           # Flask Web 应用
│   ├── app.py                     # 应用工厂（路由定义）
│   ├── models.py                  # 数据库模型（SQLite 操作）
│   ├── templates/                 # HTML 模板
│   │   ├── base.html              # 基础模板
│   │   ├── index.html             # 首页（笔记列表）
│   │   ├── note_detail.html       # 笔记详情页
│   │   └── add_note.html          # 添加笔记页
│   └── static/                    # 静态资源
│       └── css/
│           └── styles.css         # 样式文件
├── utils/                         # 工具模块
│   └── logger.py                  # 日志系统（按分钟目录、组件专属文件）
├── data/                          # SQLite 数据库文件
├── log/                           # 日志输出目录
├── run.py                         # 入口文件
└── requirements.txt               # 依赖列表
```

---

## 七、架构原则

### 7.1 完全解耦
- **Flask 与数据库解耦**：通过中间件通信
- **生产者与消费者解耦**：通过主题路由通信
- **中间件与业务解耦**：不处理业务逻辑，只负责路由

### 7.2 异步处理
- **事件驱动**：所有操作都是异步非阻塞
- **队列缓冲**：消息先入队再处理，削峰填谷
- **并行消费**：多个消费者可同时处理同一主题

### 7.3 单一职责
- **中间件**：只做消息路由
- **消费者**：只做数据库操作
- **Flask**：只做 HTTP 处理和视图渲染

### 7.4 可扩展性
- **新增事件类型**：只需添加新主题和消费者
- **水平扩展**：可部署多个中间件节点
- **消费者扩容**：同一主题可添加多个消费者实例

### 7.5 可靠性
- **线程安全**：队列和路由使用锁保护
- **持久连接**：生产者和消费者保持长连接
- **优雅关闭**：支持连接清理和资源释放

---

## 八、运行说明

### 8.1 安装依赖

```bash
pip install -r requirements.txt
```

### 8.2 启动应用

```bash
python run.py
```

### 8.3 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Flask Web | 5000 | HTTP 服务 |
| Middleware | 5001 | 消息中间件 |

---

## 九、技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| Web 框架 | Flask | 2.0+ | HTTP 处理、模板渲染 |
| 数据库 | SQLite | 内置 | 轻量级持久化存储 |
| 网络通信 | Socket | 内置 | TCP 连接管理 |
| 并发处理 | threading | 内置 | 多线程支持 |
| 日志系统 | 自定义 | - | 组件专属日志 |

---

## 许可证

本项目采用 MIT 许可证。