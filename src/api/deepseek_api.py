import requests
import os
import json
import logging
from config.setting import BASE_URL

logger = logging.getLogger(__name__)

class DeepSeekAPI:
    @staticmethod
    def get_api_key():
        """安全获取API密钥
        优先从环境变量获取，如果没有则尝试从配置文件获取，最后提示用户输入
        :return: API密钥字符串
        """
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            try:
                raise ValueError("请使用环境变量DEEPSEEK_API_KEY或运行时输入API密钥")
            except Exception:
                api_key = input('请输入DeepSeek API密钥: ')
        return api_key
    def __init__(self, api_key=None):
        """
        初始化DeepSeek API客户端
        :param api_key: DeepSeek API密钥，如果为None则尝试从环境变量、配置文件或用户输入获取
        """
        if api_key is None:
            api_key = self.get_api_key()
        
        if not api_key:
            raise ValueError("未设置API密钥，请通过以下方式设置:\n1. 设置环境变量DEEPSEEK_API_KEY\n2. 配置文件中设置API_KEY\n3. 运行时输入API密钥\n4. 通过api_key参数传入")
        self.api_key = api_key
        self.base_url = BASE_URL
        
    def _make_request(self, endpoint, method="POST", data=None):
        """
        发送API请求
        :param endpoint: API端点路径
        :param method: HTTP方法
        :param data: 请求数据
        :return: 响应数据
        """
        url = f"{self.base_url}/{endpoint}"
        # 添加调试日志
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        logger.debug(f"API请求URL: {url}")
        logger.debug(f"请求头: {headers}")
        logger.debug(f"请求体: {data}")
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data
            )
            response.raise_for_status()
            response_data = response.json()
            return {
                "choices": [{
                    "message": {
                        "reasoning_content": response_data.get('choices', [{}])[0].get('message', {}).get('reasoning_content', ''),
                        "content": response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    }
                }]
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"API请求失败: {str(e)}")
    
    def chat_completion(self, messages, model="deepseek-chat", temperature=0.7):
        """
        调用聊天补全API
        :param messages: 对话消息列表
        :param model: 使用的模型名称
        :param temperature: 生成温度
        :return: API响应
        """

        endpoint = "chat/completions"
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        response = self._make_request(endpoint, data=data)
        return {
            "choices": [{
                "message": {
                    "reasoning_content": response.get('choices', [{}])[0].get('message', {}).get('reasoning_content', ''),
                    "content": response.get('choices', [{}])[0].get('message', {}).get('content', '')
                }
            }]
        }
        
    def chat_completion_stream(self, messages, model="deepseek-chat", temperature=0.7):
        """
        调用流式聊天补全API
        :param messages: 对话消息列表
        :param model: 使用的模型名称（支持 deepseek-chat 和 deepseek-reasoner）
        :param temperature: 生成温度
        :return: 生成器，每次yield一个响应块
        """
        
        if messages is None or not isinstance(messages, list) or len(messages) == 0:
            raise ValueError("messages参数必须是有效的非空列表")
        
        # 清理消息格式
        # 移除消息内容的JSON序列化，避免双重转义
        # 校验消息角色合法性
        prev_role = None
        for msg in messages:
            current_role = msg.get('role')
            if not current_role or current_role not in ['system', 'user', 'assistant']:
                raise ValueError(f"无效的消息角色: {current_role}，允许的角色: system/user/assistant")
            
            if prev_role == current_role:
                raise ValueError(f"连续重复的消息角色: {current_role}，消息应当交替来自用户和助手")
            
            prev_role = current_role

            if 'content' in msg:
                if isinstance(msg['content'], dict):
                    msg['content'] = json.dumps(msg['content'], ensure_ascii=False)
                logger.debug(f"最终消息内容: {msg['content']}")
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        endpoint = "chat/completions"
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        
        try:
            with requests.post(url, headers=headers, json=data, stream=True) as response:
                logger.debug(f"响应状态码: {response.status_code}")
                response.raise_for_status()
                
                if not response.headers.get('Content-Type','').startswith('text/event-stream'):
                    logger.error(f"意外响应格式: {response.headers}")
                    raise Exception("Invalid response format from API")
                
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data: '):
                            json_str = decoded_line[6:]
                            if json_str == '[DONE]':
                                break
                            try:
                                chunk_data = json.loads(json_str)
                                
                                # 结构化响应数据
                                yield {
                                    "choices": [{
                                        "delta": {
                                            "reasoning_content": chunk_data.get('choices', [{}])[0].get('delta', {}).get('reasoning_content', ''),
                                            "content": chunk_data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                        }
                                    }]
                                }
                            except json.JSONDecodeError:
                                continue
        except requests.exceptions.HTTPError as e:
            error_detail = f"HTTP状态码: {response.status_code if response else '无'}\n响应头: {response.headers if response else '无'}\n响应内容: {response.text if response else '无'}"
            logger.error(f"流式API请求失败: {str(e)}\n请求头: {headers}\n请求体: {json.dumps(data)}\n{error_detail}")
            raise Exception(f"流式API请求失败: {str(e)}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求异常: {str(e)}")
            raise Exception(f"网络请求异常: {str(e)}")