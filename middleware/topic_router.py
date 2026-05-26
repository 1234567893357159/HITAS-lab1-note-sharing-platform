"""
主题路由模块

管理主题订阅关系，实现发布-订阅模式的核心功能
"""

import threading


class TopicRouter:
    """
    主题路由器
    
    维护主题到订阅者的映射关系，支持：
    - 订阅主题
    - 取消订阅
    - 获取主题的所有订阅者
    
    使用线程锁保证并发安全。
    """

    def __init__(self):
        """
        初始化主题路由器
        """
        self.subscribers = {}        # 主题 -> 订阅者列表（socket 列表）
        self.lock = threading.Lock() # 线程锁

    def subscribe(self, topic, client_socket):
        """
        订阅指定主题
        
        将客户端 socket 添加到主题的订阅者列表中。
        
        :param topic: 主题名称
        :param client_socket: 客户端连接的 socket 对象
        """
        with self.lock:
            # 如果主题不存在，创建新的订阅者列表
            if topic not in self.subscribers:
                self.subscribers[topic] = []
            # 如果客户端还没有订阅该主题，添加进去
            if client_socket not in self.subscribers[topic]:
                self.subscribers[topic].append(client_socket)

    def unsubscribe(self, topic, client_socket):
        """
        取消订阅指定主题
        
        将客户端 socket 从主题的订阅者列表中移除。
        
        :param topic: 主题名称
        :param client_socket: 客户端连接的 socket 对象
        """
        with self.lock:
            if topic in self.subscribers:
                if client_socket in self.subscribers[topic]:
                    self.subscribers[topic].remove(client_socket)
                # 如果订阅者列表为空，删除该主题
                if not self.subscribers[topic]:
                    del self.subscribers[topic]

    def get_subscribers(self, topic):
        """
        获取指定主题的所有订阅者
        
        :param topic: 主题名称
        :return: 订阅者 socket 列表的副本（避免并发修改问题）
        """
        with self.lock:
            return list(self.subscribers.get(topic, []))

    def has_subscriber(self, topic):
        """
        检查主题是否有订阅者
        
        :param topic: 主题名称
        :return: True 如果有订阅者，False 否则
        """
        with self.lock:
            return topic in self.subscribers and bool(self.subscribers[topic])