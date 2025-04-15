"""
DeepSeek API配置模块
"""

# API基础配置
BASE_URL = "https://api.deepseek.com/v1"

# 可用模型
AVAILABLE_MODELS = {
    "deepseek-chat": "DeepSeek Chat",
    "deepseek-reasoner": "DeepSeek Reasoner"
}

DEFAULT_MODEL = "deepseek-chat"
DEFAULT_TEMPERATURE = 0.7
API_KEY = ""  # 请在此处填入您的DeepSeek API密钥