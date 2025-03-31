"""
API错误处理模块，封装与DeepSeek API的错误处理逻辑
"""
from typing import Dict, Any
import time

class ErrorHandler:
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        初始化错误处理器
        :param max_retries: 最大重试次数
        :param retry_delay: 重试延迟时间(秒)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def classify_error(self, error: Exception) -> str:
        """
        错误分类
        :param error: 捕获的异常
        :return: 错误类型字符串
        """
        error_name = type(error).__name__
        if error_name == 'ConnectionError':
            return 'connection_error'
        elif error_name == 'TimeoutError':
            return 'timeout_error'
        elif 'HTTPError' in error_name:
            if hasattr(error, 'response') and getattr(error.response, 'status_code', None) == 401:
                return 'auth_error'
            return 'http_error'
        else:
            return 'unknown_error'
    
    def format_error_message(self, error_type: str, error: Exception) -> str:
        """
        格式化错误消息
        :param error_type: 错误类型
        :param error: 捕获的异常
        :return: 格式化的错误消息
        """
        messages = {
            'connection_error': '连接错误: 无法连接到API服务器',
            'timeout_error': '超时错误: 请求超时',
            'http_error': f'HTTP错误: {str(error)}',
            'auth_error': '认证错误: API密钥无效或未设置，请检查config/setting.py中的API_KEY配置',
            'unknown_error': f'未知错误: {str(error)}'
        }
        return messages.get(error_type, '未知错误')
    
    def should_retry(self, error_type: str, retry_count: int) -> bool:
        """
        判断是否应该重试
        :param error_type: 错误类型
        :param retry_count: 当前重试次数
        :return: 是否应该重试
        """
        if retry_count >= self.max_retries:
            return False
        return error_type in ['connection_error', 'timeout_error', 'auth_error']
    
    def handle_error(self, error: Exception, retry_count: int) -> Dict[str, Any]:
        """
        处理错误
        :param error: 捕获的异常
        :param retry_count: 当前重试次数
        :return: 包含处理结果的字典
        """
        error_type = self.classify_error(error)
        message = self.format_error_message(error_type, error)
        should_retry = self.should_retry(error_type, retry_count)
        
        if should_retry:
            time.sleep(self.retry_delay)
            
        return {
            'error_type': error_type,
            'message': message,
            'should_retry': should_retry
        }