"""
对话处理模块，封装与DeepSeek API的交互逻辑
"""
import io
import json
from typing import List, Dict
# 尝试兼容包模式和开发模式的导入
try:
    # 包模式导入
    from api.deepseek_api import DeepSeekAPI
    from handler.color_handler import ColorHandler
    from config.setting import DEFAULT_MODEL, DEFAULT_TEMPERATURE
except ImportError:
    # 开发模式导入
    import sys
    from pathlib import Path
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    from src.api.deepseek_api import DeepSeekAPI
    from src.handler.color_handler import ColorHandler
    from src.config.setting import DEFAULT_MODEL, DEFAULT_TEMPERATURE

class ChatHandler:
    def __init__(self):
        """
        初始化对话处理器
        """
        self.api = DeepSeekAPI(DeepSeekAPI.get_api_key())
        self.model = DEFAULT_MODEL
        self.temperature = DEFAULT_TEMPERATURE
        self.messages: List[Dict[str, str]] = []
        self.multi_mode = False
        self.interrupt_flag = False
    
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
        from .input_handler import InputHandler
        error_handler = ErrorHandler()
        retry_count = 0
        
        while True:
            try:
                if stream:
                    import sys
                    full_reply = io.StringIO()
                    DebugHandler.debug(f"开始获取流式回复，使用模型: {self.model}")
                    try:
                        # 添加标志变量，用于跟踪是否已经输出了第一个推理块和内容块的前缀
                        first_reasoning_chunk = True
                        first_content_chunk = True
                        
                        # 初始化输入处理器，用于检测用户输入
                        input_handler = InputHandler()
                        input_handler.start_listening()
                        DebugHandler.debug("已启动输入监听器")
                        
                        for chunk in self.api.chat_completion_stream(
                            messages=self.messages,
                            model=self.model,
                            temperature=self.temperature
                        ):
                            # 检查中断标志或输入中的/stop命令
                            if self.interrupt_flag or input_handler.check_for_stop_command():
                                DebugHandler.debug("检测到中断标志或/stop命令，停止输出")
                                print(ColorHandler.system_text("\n[输出已中断]\n"))
                                self.interrupt_flag = False  # 重置中断标志
                                # 确保在中断后停止输入监听器
                                input_handler.stop_listening()
                                break
                                
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
                            reasoning_chunk = first_choice['delta'].get('reasoning_content', '')
                            content_chunk = first_choice['delta'].get('content', '')
                            
                            # 空值检查和处理
                            reasoning_chunk = reasoning_chunk or ''
                            content_chunk = content_chunk or ''
                            DebugHandler.debug(f"获取推理内容: {repr(reasoning_chunk)} (长度{len(reasoning_chunk)}), 正式内容: {repr(content_chunk)} (长度{len(content_chunk)})")
                            if not reasoning_chunk and not content_chunk:
                                continue
                            
                            DebugHandler.debug(f"获取推理内容: {repr(reasoning_chunk)}, 正式内容: {repr(content_chunk)}")
                            
                            # 打印推理过程（灰色）和正式回答（原色）
                            if self.model != 'deepseek-chat' and reasoning_chunk:
                                # 只在第一个推理块前添加前缀
                                if first_reasoning_chunk:
                                    sys.stdout.write(ColorHandler.reasoning_text(f"推理过程：\n{reasoning_chunk}"))
                                    sys.stdout.flush()
                                    first_reasoning_chunk = False
                                else:
                                    sys.stdout.write(ColorHandler.reasoning_text(reasoning_chunk))
                                    sys.stdout.flush()
                            if content_chunk:
                                # 只在第一个内容块前添加前缀
                                if first_content_chunk:
                                    if self.model != 'deepseek-chat':
                                        sys.stdout.write("\n")
                                        sys.stdout.flush()
                                    sys.stdout.write(ColorHandler.assistant_text(f"最终回复：\n{content_chunk}"))
                                    sys.stdout.flush()
                                    first_content_chunk = False
                                else:
                                    sys.stdout.write(ColorHandler.assistant_text(content_chunk))
                                    sys.stdout.flush()
                            
                            full_reply.write(content_chunk if self.model == 'deepseek-chat' else reasoning_chunk + content_chunk)
                        
                        # 更新验证逻辑
                        full_reply_str = full_reply.getvalue()
                        # 处理空响应的情况
                        if not full_reply_str.strip():
                            full_reply_str = "抱歉，未能获取有效回复，请稍后重试"
                        print()
                        self.messages.append({"role": "assistant", "content": full_reply_str})
                        DebugHandler.debug("流式回复完成")
                        
                        # 停止输入监听器
                        input_handler.stop_listening()
                        DebugHandler.debug("已停止输入监听器")
                        
                        return full_reply_str
                    except Exception as e:
                        # 流式请求出错，记录错误并继续处理
                        DebugHandler.debug(f"流式请求出错: {str(e)}")
                        # 确保停止输入监听器
                        try:
                            input_handler.stop_listening()
                            DebugHandler.debug("异常情况下已停止输入监听器")
                        except Exception as input_ex:
                            DebugHandler.debug(f"停止输入监听器时出错: {str(input_ex)}")
                        raise e
                else:
                    DebugHandler.debug(f"开始获取非流式回复，使用模型: {self.model}")
                    response = self.api.chat_completion(
                        messages=self.messages,
                        model=self.model,
                        temperature=self.temperature
                    )
                    if not self.validate_response_structure(response, stream=False):
                        raise ValueError("无效的API响应结构")
                    message = response['choices'][0]['message']
                    reasoning_content = message.get('reasoning_content', '')
                    content = message.get('content', '')
                    
                    # 根据模型类型构建回复内容
                    if self.model == 'deepseek-chat':
                        assistant_reply = content
                    else:
                        # 添加分隔符，与流式模式保持一致
                        assistant_reply = reasoning_content + '最终回复：' + content
                    
                    # 处理空响应的情况
                    if not assistant_reply.strip():
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
    
    def validate_response_structure(self, data: dict, stream: bool) -> bool:
        """验证API响应结构"""
        required_keys = {
            'choices': [
                lambda x: isinstance(x, list) and len(x) > 0,
                {
                    'delta' if stream else 'message': {
                        'content': lambda x: isinstance(x, str),
                        'reasoning_content': lambda x: isinstance(x, str) if self.model == 'deepseek-reasoner' else True
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
                # 列表验证器的第一个元素是验证函数，第二个元素是子结构
                # 先验证列表本身
                if len(validator) > 0 and callable(validator[0]):
                    if not validator[0](data[key]):
                        return False
                # 如果有子结构，则验证列表中的每个元素
                if len(validator) > 1 and isinstance(validator[1], dict):
                    for item in data[key]:
                        if not self._check_data_structure(item, validator[1]):
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
        
    def interrupt_output(self) -> None:
        """中断当前输出"""
        self.interrupt_flag = True
        DebugHandler.debug("设置中断标志为True")
        
    def handle_multi(self) -> bool:
        """切换多行输入模式"""
        self.multi_mode = True
        print(ColorHandler.system_text("多行输入模式已开启"))
        if self.multi_mode:
            print(ColorHandler.system_text("请输入多行文本，输入/eof结束"))
        return True