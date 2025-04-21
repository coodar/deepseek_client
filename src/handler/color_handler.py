"""颜色处理模块，用于在终端中显示彩色文本"""

try:
    from colorama import init, Fore, Style
    init(autoreset=True)  # 自动重置颜色，避免颜色溢出
    COLOR_ENABLED = True
except ImportError:
    # 如果没有安装colorama，则使用空字符串代替颜色代码
    class DummyFore:
        def __getattr__(self, name):
            return ''
    
    class DummyStyle:
        def __getattr__(self, name):
            return ''
    
    Fore = DummyFore()
    Style = DummyStyle()
    COLOR_ENABLED = False
    print("警告: 未安装colorama库，将不会显示彩色文本。可以使用 'pip install colorama' 安装。")


class ColorHandler:
    """颜色处理类，提供各种颜色的文本输出方法"""
    
    @staticmethod
    def is_enabled() -> bool:
        """检查颜色功能是否启用"""
        return COLOR_ENABLED
    
    @staticmethod
    def user_text(text: str) -> str:
        """用户文本颜色 (青色)"""
        if text is None:
            text = ''
        return f"{Fore.CYAN}{text}{Style.RESET_ALL}"
    
    @staticmethod
    def assistant_text(text: str) -> str:
        """助手文本颜色 (品红)"""
        if COLOR_ENABLED:
            return f"{Fore.MAGENTA}{text}{Style.RESET_ALL}"
        return text

    @staticmethod
    def reasoning_text(text: str) -> str:
        """推理文本颜色 (黄色)"""
        if COLOR_ENABLED:
            return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"
        return text
    
    @staticmethod
    def system_text(text: str) -> str:
        """系统文本颜色 (黄色)"""
        if text is None:
            text = ''
        return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"
    
    @staticmethod
    def reasoning_text(text: str) -> str:
        """推理文本颜色 (灰黑色)"""
        if text is None:
            text = ''
        return f"{Fore.LIGHTBLACK_EX}{text}{Style.RESET_ALL}"

    @staticmethod
    def error_text(text: str) -> str:
        """错误文本颜色 (红色)"""
        if text is None:
            text = ''
        return f"{Fore.RED}{text}{Style.RESET_ALL}"
    
    @staticmethod
    def highlight_text(text: str) -> str:
        """高亮文本 (亮白色)"""
        if text is None:
            text = ''
        return f"{Style.BRIGHT}{text}{Style.RESET_ALL}"
    
    @staticmethod
    def stream_mode_text(text: str) -> str:
        return f"\033[92m{text}\033[0m"  # 亮绿色

    @staticmethod
    def non_stream_mode_text(text: str) -> str:
        return f"\033[93m{text}\033[0m"  # 亮黄色