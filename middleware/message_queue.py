"""
消息队列模块

实现线程安全的消息队列，用于异步消息处理
"""

import threading


class MessageQueue:
    """
    线程安全的消息队列
    
    使用 Python list 实现 FIFO（先进先出）队列，
    通过 threading.Lock 保证多线程环境下的并发安全。
    
    主要用于中间件内部的消息缓冲和异步处理。
    """

    def __init__(self):
        """
        初始化消息队列
        """
        self.queue = []              # 消息列表
        self.lock = threading.Lock() # 线程锁

    def put_message(self, message):
        """
        向队列中添加消息（线程安全）
        
        :param message: Message 对象
        """
        with self.lock:
            self.queue.append(message)

    def get_message(self):
        """
        从队列中获取消息（线程安全）
        
        :return: Message 对象，如果队列为空返回 None
        """
        with self.lock:
            if self.queue:
                return self.queue.pop(0)  # FIFO：弹出第一个元素
            return None

    def is_empty(self):
        """
        检查队列是否为空（线程安全）
        
        :return: True 如果队列为空，False 否则
        """
        with self.lock:
            return len(self.queue) == 0

    def clear(self):
        """
        清空队列（线程安全）
        """
        with self.lock:
            self.queue.clear()