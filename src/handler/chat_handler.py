"""
对话处理模块，封装与DeepSeek API的交互逻辑
"""
import io
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
                    full_reply = io.StringIO()
                    DebugHandler.debug(f"开始获取流式回复")
                    try:
                        for chunk in self.api.chat_completion_stream(
                            messages=self.messages,
                            model=self.model,
                            temperature=self.temperature
                        ):
                            if not isinstance(chunk, dict):
                                DebugHandler.debug("无效的chunk类型，跳过")
                                continue
                            if not chunk.get('choices') or not isinstance(chunk['choices'], list) or len(chunk['choices']) == 0:
                                DebugHandler.debug("chunk中缺少有效的choices数组，跳过")
                                continue
                            first_choice = chunk['choices'][0]
                            if 'delta' not in first_choice or not isinstance(first_choice['delta'], dict):
                                DebugHandler.debug("choice中缺少delta字段，跳过")
                                continue
                            chunk_content = first_choice['delta'].get('content', '')
                            print(ColorHandler.assistant_text(chunk_content), end="", flush=True)
                            full_reply.write(chunk_content)
                        full_reply_str = full_reply.getvalue()
                        # 处理空响应的情况
                        if not full_reply_str.strip():
                            full_reply_str = "抱歉，未能获取有效回复，请稍后重试"
                        print()
                        self.messages.append({"role": "assistant", "content": full_reply_str})
                        DebugHandler.debug("流式回复完成")
                        return full_reply_str
                    except Exception as e:
                        # 流式请求出错，记录错误并继续处理
                        DebugHandler.debug(f"流式请求出错: {str(e)}")
                        raise e
                else:
                    DebugHandler.debug("开始获取非流式回复")
                    response = self.api.chat_completion(
                        messages=self.messages,
                        model=self.model,
                        temperature=self.temperature
                    )
                    if not self.validate_response_structure(response):
                        raise ValueError("无效的API响应结构")
                    assistant_reply = response['choices'][0]['message']['content']
                    # 处理空响应的情况
                    if not assistant_reply:
                        assistant_reply = "抱歉，未能获取有效回复，请稍后重试"
                    self.messages.append({"role": "assistant", "content": assistant_reply})
                    DebugHandler.debug("非流式回复完成")
                    return assistant_reply
                
            except Exception as e:
                full_reply_str = ''
                error_info = error_handler.handle_error(e, retry_count)
                full_reply = io.StringIO()  # 清空临时缓存
                if not error_info['should_retry']:
                    print(ColorHandler.error_text(f"错误: {error_info['message']}"))
                    return "抱歉，处理您的请求时出错"
                
                retry_count += 1
                DebugHandler.debug(f"重试请求 (第{retry_count}次)")
    
    def validate_response_structure(self, data: dict) -> bool:
        """验证API响应结构"""
        required_keys = {
            'choices': [
                lambda x: isinstance(x, list) and len(x) > 0,
                {
                    'message': {
                        'content': lambda x: isinstance(x, str)
                    }
                }
            ]
        }
        return self._check_data_structure(data, required_keys)

    def _check_data_structure(self, data: dict, structure: dict) -> bool:
        """递归验证数据结构"""
        for key, validator in structure.items():
            if key not in data:
                return False
            
            if isinstance(validator, list):
                if not isinstance(data[key], list):
                    return False
                for item in data[key]:
                    if not self._check_data_structure(item, validator[0]):
                        return False
            elif callable(validator):
                if not validator(data[key]):
                    return False
            elif isinstance(validator, dict):
                if not isinstance(data[key], dict):
                    return False
                if not self._check_data_structure(data[key], validator):
                    return False
        return True

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