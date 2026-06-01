"""
查询消费者模块

负责处理数据库查询请求，是事件驱动架构中唯一执行数据库查询的组件

查询流程：
1. 订阅 query/request 主题接收查询请求
2. 根据查询类型执行相应的数据库操作
3. 通过 query/response 主题返回查询结果
"""

import json

from .base_consumer import MessageConsumer
from producer.producer import MessageProducer
from utils.logger import ComponentLogger


class QueryConsumer(MessageConsumer):
    """
    查询消费者
    
    订阅 query/request 主题，负责处理所有数据库查询请求：
    - get_notes: 获取所有笔记列表
    - get_note: 获取单个笔记详情
    - get_comments: 获取笔记评论列表
    - get_like_count: 获取笔记点赞数
    
    查询结果通过 query/response 主题返回给请求方
    """

    def __init__(self, host, port):
        """
        初始化查询消费者
        
        :param host: 中间件服务器地址
        :param port: 中间件服务器端口
        """
        super().__init__(host, port, "query_consumer")
        # 创建生产者用于发送查询响应（必须在 subscribe_topic 之前创建）
        self.producer = MessageProducer(host, port)
        # 订阅查询请求主题（实际向中间件发送订阅请求）
        self.subscribe_topic("query/request")
        # 记录已订阅的主题列表
        self.subscribed_topics = ['query/request']
        # 日志记录器已经在基类中初始化

    def process_message(self, message):
        """
        处理查询请求消息
        
        解析查询请求，执行数据库查询，并发送响应结果
        
        :param message: Message 对象，包含查询参数
        """
        # 只处理查询请求主题的消息
        if message.topic != "query/request":
            return

        # 提取查询参数
        content = message.content
        query_id = content.get("query_id")    # 查询唯一标识
        query_type = content.get("query_type") # 查询类型
        params = content.get("params", {})    # 查询参数

        # 记录开始处理日志
        self.logger.log(f"[QueryConsumer] 处理查询请求 - ID: {query_id}, 类型: {query_type}")

        try:
            # 执行数据库查询
            result = self.execute_query(query_type, params)
            # 将查询ID添加到结果中，用于客户端匹配响应
            result["query_id"] = query_id
            
            # 发送查询响应到中间件
            self.producer.send_message("query/response", result)
            # 记录查询完成日志
            self.logger.log(f"[QueryConsumer] 查询完成 - ID: {query_id}, 状态: {result['status']}")
        except Exception as e:
            # 处理查询异常
            self.logger.log(f"[QueryConsumer] 查询失败 - ID: {query_id}, 错误: {e}")
            # 构建错误响应
            error_result = {"status": "error", "message": str(e), "query_id": query_id}
            # 发送错误响应
            self.producer.send_message("query/response", error_result)

    def execute_query(self, query_type, params):
        """
        执行具体的数据库查询
        
        根据查询类型调用相应的数据库操作函数
        
        :param query_type: 查询类型（get_notes, get_note, get_comments, get_like_count）
        :param params: 查询参数
        :return: 查询结果字典，包含 status 和 data 字段
        """
        # 延迟导入，避免循环依赖
        from web.models import get_notes, get_note, get_comments, get_like_count
        
        # 根据查询类型执行相应操作
        if query_type == "get_notes":
            # 获取所有笔记列表
            notes = get_notes()
            return {"status": "success", "data": [dict(note) for note in notes]}
        elif query_type == "get_note":
            # 获取单个笔记详情
            note = get_note(params.get("note_id"))
            return {"status": "success", "data": dict(note) if note else None}
        elif query_type == "get_comments":
            # 获取笔记评论列表
            comments = get_comments(params.get("note_id"))
            return {"status": "success", "data": [dict(c) for c in comments]}
        elif query_type == "get_like_count":
            # 获取笔记点赞数
            count = get_like_count(params.get("note_id"))
            return {"status": "success", "data": count}
        else:
            # 未知查询类型
            return {"status": "error", "message": "Unknown query type"}

    def connect(self):
        """
        建立连接
        
        同时建立消费者连接和生产者连接
        """
        super().connect()        # 建立消费者连接
        self.producer.connect()  # 建立生产者连接

    def close(self):
        """
        关闭连接
        
        同时关闭消费者连接和生产者连接
        """
        super().close()        # 关闭消费者连接
        self.producer.close()  # 关闭生产者连接