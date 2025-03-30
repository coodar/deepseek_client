import requests
from .setting import API_KEY, BASE_URL, DEFAULT_MODEL, DEFAULT_TEMPERATURE

class DeepSeekAPI:
    def __init__(self, api_key=None):
        """
        初始化DeepSeek API客户端
        :param api_key: DeepSeek API密钥，如果为None则尝试从环境变量或用户输入获取
        """
        if api_key is None:
            api_key = os.getenv('DEEPSEEK_API_KEY')
            if not api_key:
                api_key = input('请输入DeepSeek API密钥: ')
        
        self.api_key = api_key or API_KEY
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