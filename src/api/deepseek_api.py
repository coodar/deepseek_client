import requests
import os
import json
from config.setting import BASE_URL, API_KEY

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
                api_key = API_KEY
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
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
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
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        return self._make_request("chat/completions", data=data)
        
    def chat_completion_stream(self, messages, model="deepseek-chat", temperature=0.7):
        """
        调用流式聊天补全API
        :param messages: 对话消息列表
        :param model: 使用的模型名称
        :param temperature: 生成温度
        :return: 生成器，每次yield一个响应块
        """
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        
        try:
            with requests.post(url, headers=headers, json=data, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data: '):
                            json_str = decoded_line[6:]
                            if json_str == '[DONE]':
                                break
                            try:
                                yield json.loads(json_str)
                            except json.JSONDecodeError:
                                continue
        except requests.exceptions.RequestException as e:
            raise Exception(f"流式API请求失败: {str(e)}")