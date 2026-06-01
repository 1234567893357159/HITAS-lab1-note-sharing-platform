"""
通知消费者模块

负责处理笔记点赞、评论和删除事件，生成用户通知并保存到数据库
"""

from .base_consumer import MessageConsumer
from web.models import add_notification, delete_note, add_like, add_comment
from utils.logger import ComponentLogger


class NoticeConsumer(MessageConsumer):
    """
    通知消费者
    
    订阅 note/like、note/comment 和 note/delete 主题，负责处理用户互动事件：
    1. 当笔记被点赞时，执行点赞操作并生成点赞通知
    2. 当笔记被评论时，执行评论操作并生成评论通知
    3. 当笔记被删除时，从数据库删除笔记记录
    
    这是实现用户通知系统和笔记管理的核心组件
    """

    def __init__(self, host, port):
        """
        初始化通知消费者
        
        :param host: 中间件服务器地址
        :param port: 中间件服务器端口
        """
        super().__init__(host, port, "notice_consumer")
        # 订阅点赞、评论和删除主题（实际向中间件发送订阅请求）
        self.subscribe_topic("note/like")
        self.subscribe_topic("note/comment")
        self.subscribe_topic("note/delete")
        # 记录已订阅的主题列表
        self.subscribed_topics = ['note/like', 'note/comment', 'note/delete']
        # 日志记录器已经在基类中初始化

    def process_message(self, message):
        """
        处理互动消息
        
        根据消息主题类型执行相应操作：
        - note/like: 执行点赞操作并生成点赞通知
        - note/comment: 执行评论操作并生成评论通知
        - note/delete: 删除笔记记录
        
        :param message: Message 对象，包含互动数据
        """
        if message.topic == "note/like":
            # 处理点赞事件
            content = message.content
            note_id = content["note_id"]
            user_id = content.get("user_id")
            # 执行点赞数据库操作
            add_like(note_id, user_id)
            # 添加点赞通知到数据库
            add_notification(
                note_id=note_id,
                event_type="like",
                message=f"用户 {user_id} 点赞了你的笔记"
            )
            self.logger.log(f"[NoticeConsumer] 已处理点赞 - 笔记ID: {note_id}, 用户ID: {user_id}")
            
        elif message.topic == "note/comment":
            # 处理评论事件
            content = message.content
            note_id = content["note_id"]
            user_id = content.get("user_id")
            comment_text = content.get("comment_text")
            # 执行评论数据库操作
            add_comment(note_id, user_id, comment_text)
            # 添加评论通知到数据库
            add_notification(
                note_id=note_id,
                event_type="comment",
                message=f"用户 {user_id} 评论了你的笔记：{comment_text}"
            )
            self.logger.log(f"[NoticeConsumer] 已处理评论 - 笔记ID: {note_id}, 用户ID: {user_id}")
            
        elif message.topic == "note/delete":
            # 处理删除事件
            content = message.content
            note_id = content.get("note_id")
            # 从数据库删除笔记
            delete_note(note_id)
            self.logger.log(f"[NoticeConsumer] 已删除笔记 - 笔记ID: {note_id}")