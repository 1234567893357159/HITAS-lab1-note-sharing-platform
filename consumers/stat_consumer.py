"""
统计消费者模块

负责处理笔记互动事件，更新笔记的热度分数
"""

from .base_consumer import MessageConsumer
from web.models import update_note_heat
from utils.logger import ComponentLogger


class StatConsumer(MessageConsumer):
    """
    统计消费者
    
    订阅 note/like 和 note/comment 主题，负责更新笔记热度：
    1. 点赞事件：增加 2 热度
    2. 评论事件：增加 3 热度
    
    热度分数用于排序和推荐热门笔记
    """

    def __init__(self, host, port):
        """
        初始化统计消费者
        
        :param host: 中间件服务器地址
        :param port: 中间件服务器端口
        """
        super().__init__(host, port)
        # 获取组件专属日志记录器
        self.logger = ComponentLogger.get_logger("stat_consumer")
        # 订阅点赞和评论主题（实际向中间件发送订阅请求）
        self.subscribe_topic("note/like")
        self.subscribe_topic("note/comment")
        # 记录已订阅的主题列表
        self.subscribed_topics = ['note/like', 'note/comment']

    def process_message(self, message):
        """
        处理互动消息并更新热度
        
        根据消息类型更新笔记热度：
        - note/like: 热度 +2
        - note/comment: 热度 +3
        
        :param message: Message 对象，包含互动数据
        """
        content = message.content
        
        if message.topic == "note/like":
            # 点赞事件：增加 2 热度
            update_note_heat(content["note_id"], 2)
            self.logger.log(f"[StatConsumer] 已处理点赞热度 {content.get('note_id')}")
        elif message.topic == "note/comment":
            # 评论事件：增加 3 热度
            update_note_heat(content["note_id"], 3)
            self.logger.log(f"[StatConsumer] 已处理评论热度 {content.get('note_id')}")