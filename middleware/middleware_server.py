"""
中间件服务器模块

消息中间件的核心组件，负责：
1. TCP 连接管理
2. 消息接收和路由
3. 查询请求处理
4. 发布-订阅模式实现

架构设计：
- 主线程：监听端口，接收客户端连接
- 工作线程：每个连接一个线程处理消息
- 分发线程：负责将消息路由到订阅者
"""

import json
import socket
import threading
import time

from .message import Message
from .message_queue import MessageQueue
from .topic_router import TopicRouter
from utils.logger import ComponentLogger
from utils.traffic_monitor import TrafficMonitor


class MiddlewareServer:
    """
    消息中间件服务器
    
    核心功能：
    - 接收客户端连接（生产者、消费者、查询客户端）
    - 处理三种消息类型：查询请求、订阅请求、发布消息
    - 使用队列实现异步消息分发
    - 通过主题路由实现发布-订阅模式
    """

    def __init__(self, host="127.0.0.1", port=5001):
        """
        初始化中间件服务器
        
        :param host: 监听地址，默认 127.0.0.1
        :param port: 监听端口，默认 5001
        """
        self.host = host                        # 监听地址
        self.port = port                        # 监听端口
        self.server_socket = None               # 服务器 socket
        self.msg_queue = MessageQueue()         # 统一消息队列
        self.router = TopicRouter()             # 主题路由器
        self.is_running = False                 # 运行状态标志
        self.dispatcher_thread = None           # 消息分发线程
        self.logger = ComponentLogger.get_logger("middleware")  # 日志记录器
        self.traffic_monitor = TrafficMonitor()  # 流量监控器
        self.traffic_monitor.initialize()

    def start_server(self):
        """
        启动中间件服务器
        
        创建 TCP socket，启动连接接收线程和消息分发线程
        """
        self.is_running = True
        
        # 创建 TCP socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置端口复用
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 绑定地址和端口
        self.server_socket.bind((self.host, self.port))
        # 开始监听（最大 10 个排队连接）
        self.server_socket.listen(10)

        # 启动连接接收线程
        accept_thread = threading.Thread(target=self.accept_connections, daemon=True)
        accept_thread.start()

        # 启动统一消息分发线程
        self.dispatcher_thread = threading.Thread(target=self.dispatch_messages, daemon=True)
        self.dispatcher_thread.start()

        self.logger.log(f"[Middleware] 服务已启动 {self.host}:{self.port}")

    def accept_connections(self):
        """
        接受客户端连接
        
        持续监听端口，每收到一个连接就创建新线程处理
        """
        while self.is_running:
            try:
                # 接受连接
                client_socket, addr = self.server_socket.accept()
                self.logger.log(f"[Middleware] 新节点加入: {addr}")
                self.traffic_monitor.record_connection_open()
            except OSError:
                # 服务器关闭时会抛出异常
                break
            # 创建新线程处理客户端消息
            threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True).start()

    def handle_client(self, client_socket, addr):
        """
        处理客户端消息
        
        解析客户端发送的消息，根据类型进行不同处理：
        - query: 查询请求，放入查询队列
        - subscribe: 订阅请求，注册到主题路由
        - publish: 发布消息，放入消息队列
        
        :param client_socket: 客户端 socket
        :param addr: 客户端地址
        """
        buffer = ""  # 缓冲区，处理 TCP 粘包
        try:
            while self.is_running:
                # 接收数据（最多 4096 字节）
                data = client_socket.recv(4096)
                if not data:
                    # 连接被关闭
                    break
                buffer += data.decode("utf-8")
                # 按换行符分割消息
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip():
                        continue
                    # 解析 JSON 消息
                    payload = json.loads(line)
                    msg_type = payload.get("type")
                    
                    if msg_type == "query":
                        # 处理查询请求
                        query_id = payload.get("query_id", str(time.time()))
                        query_type = payload.get("query_type")
                        params = payload.get("params", {})
                        query_msg = {
                            "query_id": query_id,
                            "query_type": query_type,
                            "params": params
                        }
                        self.msg_queue.put_message(Message("query/request", query_msg))
                        self.traffic_monitor.record_query_received(query_type)
                    
                    elif msg_type == "subscribe":
                        # 处理订阅请求
                        self.router.subscribe(payload["topic"], client_socket)
                    
                    elif msg_type == "publish" or ("topic" in payload and "content" in payload):
                        # 处理发布消息
                        message = Message(payload["topic"], payload["content"])
                        self.msg_queue.put_message(message)
                        self.traffic_monitor.record_message_received(message.topic)
        finally:
            # 清理连接
            self._cleanup_socket(client_socket, addr)

    def dispatch_messages(self):
        """
        分发所有类型的消息
        
        从统一消息队列获取消息，路由到所有订阅者
        """
        while self.is_running:
            # 记录队列深度
            self.traffic_monitor.record_queue_depth(len(self.msg_queue.queue))
            
            message = self.msg_queue.get_message()
            if message:
                subscribers = self.router.get_subscribers(message.topic)
                self.send_to_consumers(subscribers, message)
                if message.topic.startswith("query/"):
                    query_type = message.content.get("query_type", "unknown")
                    self.traffic_monitor.record_query_dispatched(query_type)
                else:
                    self.traffic_monitor.record_message_dispatched(message.topic, message.message_id)
            else:
                time.sleep(0.05)

    def handle_query(self, query_type, params):
        """
        处理数据库查询（备用方法）
        
        直接执行数据库查询并返回结果，用于同步查询模式。
        当前架构使用 QueryConsumer 处理查询，此方法保留备用。
        
        :param query_type: 查询类型
        :param params: 查询参数
        :return: 查询结果字典
        """
        from web.models import get_notes, get_note, get_comments, get_like_count
        
        try:
            if query_type == "get_notes":
                notes = get_notes()
                return {"status": "success", "data": [dict(note) for note in notes]}
            elif query_type == "get_note":
                note = get_note(params.get("note_id"))
                return {"status": "success", "data": dict(note) if note else None}
            elif query_type == "get_comments":
                comments = get_comments(params.get("note_id"))
                return {"status": "success", "data": [dict(c) for c in comments]}
            elif query_type == "get_like_count":
                count = get_like_count(params.get("note_id"))
                return {"status": "success", "data": count}
            else:
                return {"status": "error", "message": "Unknown query type"}
        except Exception as e:
            self.logger.log(f"[Middleware] 查询失败 - 类型: {query_type}, 错误: {e}")
            return {"status": "error", "message": str(e)}

    def _cleanup_socket(self, client_socket, addr):
        """
        清理客户端连接
        
        从所有主题中取消订阅，并关闭 socket
        
        :param client_socket: 客户端 socket
        :param addr: 客户端地址
        """
        # 获取所有主题并取消订阅
        topics = list(self.router.subscribers.keys())
        for topic in topics:
            self.router.unsubscribe(topic, client_socket)
        # 关闭 socket
        try:
            client_socket.close()
        except Exception:
            pass
        self.logger.log(f"[Middleware] 节点退出: {addr}")
        self.traffic_monitor.record_connection_close()

    def start_dispatcher(self):
        """
        启动消息分发器（备用方法）
        
        如果分发线程未运行，启动它
        """
        if not self.dispatcher_thread or not self.dispatcher_thread.is_alive():
            self.dispatcher_thread = threading.Thread(target=self.dispatch_messages, daemon=True)
            self.dispatcher_thread.start()

    def send_to_consumers(self, subscribers, message):
        """
        发送消息给所有订阅者
        
        :param subscribers: 订阅者 socket 列表
        :param message: Message 对象
        """
        if subscribers:
            self.logger.log(f"[Middleware] 发送消息类型: {message.topic} 给 {len(subscribers)} 个订阅者")
        for subscriber in subscribers:
            try:
                subscriber.sendall((message.to_json() + "\n").encode("utf-8"))
            except Exception:
                # 发送失败，取消订阅
                self.router.unsubscribe(message.topic, subscriber)

    def stop_server(self):
        """
        停止服务器
        
        设置运行标志为 False，关闭服务器 socket
        """
        self.is_running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        self.logger.log("[Middleware] 服务已停止")