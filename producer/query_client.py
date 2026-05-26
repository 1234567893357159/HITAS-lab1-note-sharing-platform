"""
查询客户端模块

负责通过消息中间件向 QueryConsumer 发送查询请求，并接收响应

查询流程：
1. 建立与中间件的连接
2. 订阅 query/response 主题（用于接收查询结果）
3. 发送查询请求（query/request）
4. 异步监听响应，通过 query_id 匹配结果
"""

import json
import socket
import threading
import time

from utils.logger import ComponentLogger


class QueryClient:
    """
    查询客户端
    
    通过中间件与 QueryConsumer 通信，执行数据库查询操作。
    
    支持的查询类型：
    - get_notes: 获取所有笔记列表
    - get_note: 获取单个笔记详情
    - get_comments: 获取笔记评论列表
    - get_like_count: 获取笔记点赞数
    """

    def __init__(self, host="127.0.0.1", port=5001):
        """
        初始化查询客户端
        
        :param host: 中间件服务器地址，默认 127.0.0.1
        :param port: 中间件服务器端口，默认 5001
        """
        self.host = host                # 中间件地址
        self.port = port                # 中间件端口
        self.socket = None              # TCP 连接套接字
        self.logger = ComponentLogger.get_logger("query_client")  # 日志记录器
        self.is_listening = False       # 是否正在监听响应
        self.listen_thread = None       # 响应监听线程
        self.pending_queries = {}       # 待处理查询 {query_id: result}
        self.lock = threading.Lock()    # 线程锁（保护 pending_queries）

    def connect(self):
        """
        建立与中间件的连接
        
        如果已存在连接则直接返回，避免重复连接。
        连接建立后自动订阅 query/response 主题并启动监听线程。
        """
        if self.socket:
            return
        # 创建 TCP 连接，超时时间 5 秒
        self.socket = socket.create_connection((self.host, self.port), timeout=5)
        # 设置接收超时为 1 秒，避免线程阻塞
        self.socket.settimeout(1)
        self.logger.log(f"[QueryClient] 已连接到中间件 {self.host}:{self.port}")
        # 订阅查询响应主题
        self.subscribe_response()
        # 启动响应监听线程
        self.start_listening()

    def subscribe_response(self):
        """
        订阅查询响应主题
        
        向中间件发送订阅请求，以便接收 query/response 消息
        """
        request = {"type": "subscribe", "topic": "query/response"}
        self.socket.sendall((json.dumps(request) + "\n").encode("utf-8"))
        self.logger.log(f"[QueryClient] 已订阅查询结果主题")

    def start_listening(self):
        """
        启动响应监听线程
        
        创建守护线程来接收和处理查询响应
        """
        if self.listen_thread and self.listen_thread.is_alive():
            return
        self.is_listening = True
        self.listen_thread = threading.Thread(target=self.receive_response, daemon=True)
        self.listen_thread.start()

    def receive_response(self):
        """
        接收响应的主循环
        
        持续监听中间件发送的查询响应，将结果存入 pending_queries 字典
        """
        buffer = ""  # 缓冲区，处理 TCP 粘包
        while self.is_listening:
            try:
                # 接收数据（最多 4096 字节）
                data = self.socket.recv(4096)
                if not data:
                    # 连接被关闭
                    break
                buffer += data.decode("utf-8")
                # 按换行符分割消息
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip():
                        continue
                    try:
                        # 解析响应消息
                        payload = json.loads(line)
                        if payload.get("topic") == "query/response":
                            content = payload.get("content", {})
                            query_id = content.get("query_id")
                            # 将结果存入 pending_queries（线程安全）
                            with self.lock:
                                if query_id in self.pending_queries:
                                    self.pending_queries[query_id] = content
                    except json.JSONDecodeError:
                        # 忽略无效 JSON
                        continue
            except socket.timeout:
                # 超时是正常的，继续监听
                continue
            except Exception as e:
                self.logger.log(f"[QueryClient] 接收响应失败: {e}")
                break
        # 清理连接
        self.close()

    def query(self, query_type, params=None):
        """
        执行数据库查询
        
        :param query_type: 查询类型（get_notes, get_note, get_comments, get_like_count）
        :param params: 查询参数（字典格式）
        :return: 查询结果字典，包含 status 和 data 字段
        """
        # 生成唯一查询 ID
        query_id = str(time.time())
        # 构建查询请求
        payload = {
            "type": "query",
            "query_id": query_id,
            "query_type": query_type,
            "params": params or {}
        }

        # 确保已连接
        self.connect()
        
        # 注册待处理查询（线程安全）
        with self.lock:
            self.pending_queries[query_id] = None

        try:
            # 发送查询请求
            self.socket.sendall((json.dumps(payload) + "\n").encode("utf-8"))
            self.logger.log(f"[QueryClient] 发送查询请求 - ID: {query_id}, 类型: {query_type}")

            # 等待响应（最多 10 秒超时）
            timeout = 10
            start_time = time.time()
            while time.time() - start_time < timeout:
                with self.lock:
                    result = self.pending_queries.get(query_id)
                    if result is not None:
                        # 找到结果，移除并返回
                        del self.pending_queries[query_id]
                        self.logger.log(f"[QueryClient] 收到查询结果 - ID: {query_id}, 状态: {result['status']}")
                        return result
                time.sleep(0.1)

            # 超时处理
            with self.lock:
                del self.pending_queries[query_id]
            raise Exception("查询超时")

        except Exception as e:
            # 查询失败处理
            self.logger.log(f"[QueryClient] 查询失败 - ID: {query_id}, 错误: {e}")
            with self.lock:
                self.pending_queries.pop(query_id, None)
            self.close()
            return {"status": "error", "message": str(e)}

    def close(self):
        """
        关闭连接并清理资源
        """
        self.is_listening = False
        if self.socket:
            try:
                self.socket.close()
                self.logger.log(f"[QueryClient] 已断开与中间件的连接")
            except Exception:
                pass
            self.socket = None