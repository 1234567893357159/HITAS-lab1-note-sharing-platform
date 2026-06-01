"""
消费者基类模块

定义所有消费者的通用行为和接口，子类需要实现具体的消息处理逻辑
"""

import json
import socket
import threading
import time

from middleware.message import Message
from utils.logger import ComponentLogger


class MessageConsumer:
    """
    消息消费者基类
    
    提供与消息中间件通信的基础功能，包括连接管理、主题订阅、消息接收等。
    子类必须实现 process_message 方法来处理具体的业务逻辑。
    """

    def __init__(self, host="127.0.0.1", port=5001, component_name="base_consumer"):
        """
        初始化消费者
        
        :param host: 中间件服务器地址，默认 127.0.0.1
        :param port: 中间件服务器端口，默认 5001
        :param component_name: 组件名称，用于日志记录
        """
        self.middleware_host = host    # 中间件地址
        self.middleware_port = port    # 中间件端口
        self.socket = None             # TCP 连接套接字
        self.subscribed_topics = []    # 已订阅的主题列表
        self.is_listening = False      # 是否正在监听消息
        self.listen_thread = None      # 监听线程
        self.producer = None           # 用于发送响应的生产者（可选）
        self.component_name = component_name  # 组件名称
        self.logger = ComponentLogger.get_logger(component_name)  # 日志记录器

    def connect(self):
        """
        建立与中间件的 TCP 连接
        
        如果已存在连接则直接返回，避免重复连接
        """
        if self.socket:
            self.logger.log(f"[{self.component_name}] 已存在连接，跳过连接建立")
            return
        try:
            # 创建 TCP 连接，超时时间 5 秒
            self.socket = socket.create_connection((self.middleware_host, self.middleware_port), timeout=5)
            # 设置接收超时为 1 秒，避免线程阻塞
            self.socket.settimeout(1)
            self.logger.log(f"[{self.component_name}] 已连接到中间件 {self.middleware_host}:{self.middleware_port}")
        except Exception as e:
            self.logger.log(f"[{self.component_name}] 连接中间件失败: {e}")
            raise

    def subscribe_topic(self, topic):
        """
        订阅指定主题
        
        :param topic: 要订阅的主题名称
        """
        self.connect()  # 确保已连接
        try:
            # 构建订阅请求消息
            request = {"type": "subscribe", "topic": topic}
            # 发送订阅请求（JSON 格式 + 换行符分隔）
            self.socket.sendall((json.dumps(request, ensure_ascii=False) + "\n").encode("utf-8"))
            # 记录已订阅的主题
            if topic not in self.subscribed_topics:
                self.subscribed_topics.append(topic)
                self.logger.log(f"[{self.component_name}] 已订阅主题: {topic}")
            else:
                self.logger.log(f"[{self.component_name}] 主题 {topic} 已订阅，跳过重复订阅")
        except Exception as e:
            self.logger.log(f"[{self.component_name}] 订阅主题 {topic} 失败: {e}")
            raise

    def start_listening(self):
        """
        启动消息监听线程
        
        创建守护线程来接收和处理来自中间件的消息
        """
        # 如果监听线程已在运行，则直接返回
        if self.listen_thread and self.listen_thread.is_alive():
            self.logger.log(f"[{self.component_name}] 监听线程已在运行，跳过启动")
            return
        self.is_listening = True
        # 创建守护线程执行 receive_message 方法
        self.listen_thread = threading.Thread(target=self.receive_message, daemon=True)
        self.listen_thread.start()
        self.logger.log(f"[{self.component_name}] 消息监听线程已启动")

    def receive_message(self):
        """
        接收消息的主循环
        
        持续监听中间件发送的消息，处理 TCP 粘包问题，
        将收到的数据解析为 Message 对象并交给 process_message 处理
        """
        self.logger.log(f"[{self.component_name}] 开始接收消息...")
        buffer = ""  # 缓冲区，用于处理粘包
        while self.is_listening:
            try:
                # 接收数据（最多 4096 字节）
                data = self.socket.recv(4096)
                if not data:
                    # 连接被关闭
                    self.logger.log(f"[{self.component_name}] 连接被关闭，退出消息接收循环")
                    break
                # 将数据追加到缓冲区
                buffer += data.decode("utf-8")
                # 按换行符分割消息（处理一条或多条消息）
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip():
                        continue
                    # 将 JSON 字符串解析为 Message 对象
                    message = Message.from_json(line)
                    self.logger.log(f"[{self.component_name}] 接收到消息 - 主题: {message.topic}")
                    # 调用子类实现的 process_message 处理消息
                    self.process_message(message)
            except socket.timeout:
                # 超时是正常的，继续循环监听
                continue
            except Exception as e:
                # 发生错误，记录错误并退出循环
                self.logger.log(f"[{self.component_name}] 接收消息时发生错误: {e}")
                break
        # 清理连接
        self.logger.log(f"[{self.component_name}] 停止接收消息，准备关闭连接")
        self.close()

    def process_message(self, message):
        """
        处理消息（必须由子类实现）
        
        :param message: Message 对象，包含主题和内容
        :raises NotImplementedError: 如果子类未实现此方法
        """
        raise NotImplementedError("子类必须实现 process_message")

    def close(self):
        """
        关闭连接并清理资源
        """
        self.logger.log(f"[{self.component_name}] 开始关闭连接...")
        self.is_listening = False
        if self.socket:
            try:
                self.socket.close()
                self.logger.log(f"[{self.component_name}] 连接已关闭")
            except Exception as e:
                self.logger.log(f"[{self.component_name}] 关闭连接时发生错误: {e}")
            self.socket = None
        else:
            self.logger.log(f"[{self.component_name}] 没有活动连接需要关闭")
        self.logger.log(f"[{self.component_name}] 连接关闭完成")