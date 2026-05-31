"""
消息生产者模块

负责向消息中间件发送事件消息（如发布、点赞、评论）
"""

import json
import socket

from middleware.message import Message
from utils.logger import ComponentLogger


class MessageProducer:
    """
    消息生产者
    
    负责将业务事件发送到中间件，支持持久化连接和消息发布。
    
    使用场景：
    - Flask 发布笔记时发送 note/publish 消息
    - 用户点赞时发送 note/like 消息
    - 用户评论时发送 note/comment 消息
    """

    def __init__(self, host="127.0.0.1", port=5001):
        """
        初始化消息生产者
        
        :param host: 中间件服务器地址，默认 127.0.0.1
        :param port: 中间件服务器端口，默认 5001
        """
        self.middleware_host = host  # 中间件地址
        self.middleware_port = port  # 中间件端口
        self.socket = None           # TCP 连接套接字
        self.logger = ComponentLogger.get_logger("producer")  # 日志记录器

    def connect(self):
        """
        建立与中间件的 TCP 连接
        
        如果已存在连接则直接返回，避免重复连接（持久化连接）
        """
        if self.socket:
            return
        # 创建 TCP 连接，超时时间 5 秒
        self.socket = socket.create_connection((self.middleware_host, self.middleware_port), timeout=5)
        self.logger.log(f"[Producer] 已连接到中间件 {self.middleware_host}:{self.middleware_port}")

    def send_message(self, topic, content):
        """
        发送消息到中间件
        
        :param topic: 消息主题（如 note/publish, note/like）
        :param content: 消息内容（字典格式）
        :raises Exception: 如果发送失败
        """
        # 确保已连接
        self.connect()
        try:
            # 创建 Message 对象
            message = Message(topic, content)
            # 发送消息（JSON 格式 + 换行符分隔）
            self.socket.sendall((message.to_json() + "\n").encode("utf-8"))
        except Exception as e:
            # 发送失败，记录日志并关闭连接
            self.logger.log(f"[Producer] 发送消息失败: {e}")
            self.close()
            raise  # 重新抛出异常，让调用方处理

    def close(self):
        """
        关闭连接并清理资源
        """
        if self.socket:
            try:
                self.socket.close()
                self.logger.log(f"[Producer] 已断开与中间件的连接")
            except Exception:
                pass
            self.socket = None