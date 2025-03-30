"""
对话处理模块，封装与DeepSeek API的交互逻辑
"""
from typing import List, Dict
from .deepseek_api import DeepSeekAPI

class ChatHandler:
    def __init__(self, api_key: str = None, model: str = "deepseek-chat", temperature: float = 0.7):
        """
        初始化对话处理器
        :param api_key: API密钥
        :param model: 使用的模型名称
        :param temperature: 生成温度
        """
        self.api = DeepSeekAPI(api_key)
        self.model = model
        self.temperature = temperature
        self.messages: List[Dict[str, str]] = []
    
    def add_user_message(self, content: str) -> None:
        """添加用户消息到对话历史"""
        self.messages.append({"role": "user", "content": content})
    
    def get_assistant_reply(self) -> str:
        """
        获取助手回复
        :return: 助手回复内容
        """
        response = self.api.chat_completion(
            messages=self.messages,
            model=self.model,
            temperature=self.temperature
        )
        
        assistant_reply = response.get('choices', [{}])[0].get('message', {}).get('content', '')
        self.messages.append({"role": "assistant", "content": assistant_reply})
        return assistant_reply
    
    def reset_conversation(self) -> None:
        """重置对话历史"""
        self.messages = []