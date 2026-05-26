"""
消息模块

定义消息数据结构和序列化/反序列化方法
"""

import json
import uuid
from datetime import datetime


class Message:
    """
    消息类
    
    封装消息的核心数据，包括主题、内容、时间戳和唯一标识。
    支持 JSON 序列化和反序列化，便于在网络间传输。
    """

    def __init__(self, topic, content):
        """
        初始化消息
        
        :param topic: 消息主题（如 note/publish, query/request）
        :param content: 消息内容（字典格式）
        """
        self.topic = topic          # 消息主题
        self.content = content      # 消息内容
        self.timestamp = datetime.now().isoformat()  # 创建时间戳
        self.message_id = str(uuid.uuid4())  # 唯一消息ID

    def to_json(self):
        """
        将消息序列化为 JSON 字符串
        
        :return: JSON 格式的消息字符串
        """
        return json.dumps({
            "topic": self.topic,
            "content": self.content,
            "timestamp": self.timestamp,
            "message_id": self.message_id
        }, ensure_ascii=False)

    @staticmethod
    def from_json(json_str):
        """
        从 JSON 字符串反序列化为 Message 对象
        
        :param json_str: JSON 格式的消息字符串（支持 bytes 或 str）
        :return: Message 对象
        """
        # 如果是字节类型，先解码为字符串
        if isinstance(json_str, bytes):
            json_str = json_str.decode("utf-8")
        # 解析 JSON
        data = json.loads(json_str)
        # 创建 Message 对象
        message = Message(data["topic"], data["content"])
        # 恢复时间戳和消息ID（如果存在）
        message.timestamp = data.get("timestamp", message.timestamp)
        message.message_id = data.get("message_id", message.message_id)
        return message