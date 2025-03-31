"""
对话处理模块，封装与DeepSeek API的交互逻辑
"""
import json
from typing import List, Dict
from api.deepseek_api import DeepSeekAPI
from handler.color_handler import ColorHandler

class ChatHandler:
    def __init__(self):
        """
        初始化对话处理器
        """
        from config.setting import DEFAULT_MODEL, DEFAULT_TEMPERATURE
        self.api = DeepSeekAPI(DeepSeekAPI.get_api_key())
        self.model = DEFAULT_MODEL
        self.temperature = DEFAULT_TEMPERATURE
        self.messages: List[Dict[str, str]] = []
        self.multi_mode = False
    
    def add_user_message(self, content: str) -> None:
        """添加用户消息到对话历史"""
        self.messages.append({"role": "user", "content": content})
    
    def get_assistant_reply(self, stream: bool = True) -> str:
        """
        获取助手回复
        :param stream: 是否使用流式输出
        :return: 助手回复内容
        """
        from .error_handler import ErrorHandler
        from .debug_handler import DebugHandler
        error_handler = ErrorHandler()
        retry_count = 0
        
        while True:
            try:
                if stream:
                    full_reply = ""
                    DebugHandler.debug(f"开始获取流式回复")
                    for chunk in self.api.chat_completion_stream(
                        messages=self.messages,
                        model=self.model,
                        temperature=self.temperature
                    ):
                        chunk_content = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
                        print(ColorHandler.assistant_text(chunk_content), end="", flush=True)
                        full_reply += chunk_content
                    print()
                    self.messages.append({"role": "assistant", "content": full_reply})
                    DebugHandler.debug("流式回复完成")
                    return full_reply
                else:
                    DebugHandler.debug("开始获取非流式回复")
                    response = self.api.chat_completion(
                        messages=self.messages,
                        model=self.model,
                        temperature=self.temperature
                    )
                    assistant_reply = response.get('choices', [{}])[0].get('message', {}).get('content', '')
                    self.messages.append({"role": "assistant", "content": assistant_reply})
                    DebugHandler.debug("非流式回复完成")
                    return assistant_reply
                
            except Exception as e:
                error_info = error_handler.handle_error(e, retry_count)
                if not error_info['should_retry']:
                    print(ColorHandler.error_text(f"错误: {error_info['message']}"))
                    return "抱歉，处理您的请求时出错"
                
                retry_count += 1
                DebugHandler.debug(f"重试请求 (第{retry_count}次)")
    
    def reset_conversation(self) -> None:
        """重置对话历史"""
        self.messages = []
        
    def handle_multi(self) -> bool:
        """切换多行输入模式"""
        self.multi_mode = True
        print(ColorHandler.system_text("多行输入模式已开启"))
        if self.multi_mode:
            print(ColorHandler.system_text("请输入多行文本，输入/eof结束"))
        return True