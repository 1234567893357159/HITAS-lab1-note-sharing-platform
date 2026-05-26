"""
审核消费者模块

负责处理笔记发布事件，验证并保存发布的笔记到数据库
"""

from .base_consumer import MessageConsumer
from web.models import save_published_note, save_publish_log
from utils.logger import ComponentLogger


class AuditConsumer(MessageConsumer):
    """
    审核消费者
    
    订阅 note/publish 主题，负责处理笔记发布事件：
    1. 验证笔记内容
    2. 将笔记保存到数据库
    3. 记录发布日志
    
    这是事件驱动架构中处理业务逻辑的关键组件之一
    """

    def __init__(self, host, port):
        """
        初始化审核消费者
        
        :param host: 中间件服务器地址
        :param port: 中间件服务器端口
        """
        super().__init__(host, port)
        # 订阅笔记发布主题
        self.subscribe_topic("note/publish")
        # 获取组件专属日志记录器
        self.logger = ComponentLogger.get_logger("audit_consumer")

    def process_message(self, message):
        """
        处理发布消息
        
        当收到 note/publish 主题的消息时，执行以下操作：
        1. 保存笔记到数据库
        2. 记录发布日志
        3. 输出处理日志
        
        :param message: Message 对象，包含笔记内容
        """
        # 只处理 note/publish 主题的消息
        if message.topic != "note/publish":
            return
        
        # 提取消息内容（笔记数据）
        content = message.content
        
        # 保存笔记到数据库
        save_published_note(content)
        
        # 记录发布日志
        save_publish_log(content)
        
        # 输出处理日志
        self.logger.log(f"[AuditConsumer] 已审核并保存笔记 {content.get('note_id')}")