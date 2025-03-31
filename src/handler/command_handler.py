"""
命令处理模块，专门处理用户输入的命令
"""
import json
from typing import List, Dict
from handler.debug_handler import DebugHandler
from handler.color_handler import ColorHandler

DebugHandler.debug(f"json模块已导入，版本: {json.__version__}")

class CommandHandler:
    def __init__(self, chat_handler=None):
        self.chat_handler = chat_handler
        self.commands = {
            '/quit': self.handle_quit,
            '/stream': self.handle_stream_mode,
            '/help': self.handle_help,
            '/debug': self.handle_debug,
            '/multi': self.handle_multi
        }
        self.stream_mode = True
    
    def handle_command(self, user_input: str) -> bool:
        """
        处理用户输入的命令
        :param user_input: 用户输入
        :return: 是否继续对话
        """
        # 严格检查输入是否以斜杠开头
        normalized_input = user_input.lower().strip()
        DebugHandler.debug(f"处理用户输入，原始输入: '{user_input}', 标准化后: '{normalized_input}'")
        if not normalized_input.startswith('/'):
            return True
            
        command_func = self.commands.get(normalized_input)
        DebugHandler.debug(f"查找命令处理函数，命令: '{normalized_input}', 找到函数: {command_func}")
        if command_func:
            return command_func()
        DebugHandler.debug(f"未找到命令处理函数: '{normalized_input}'")
        return True
    
    def handle_quit(self) -> bool:
        """处理退出命令"""
        print(ColorHandler.system_text("正在退出..."))
        return False
        
    def handle_stream_mode(self) -> bool:
        """切换流式输出模式"""
        self.stream_mode = not self.stream_mode
        print(ColorHandler.system_text(f"流式输出模式已{'开启' if self.stream_mode else '关闭'}"))
        return True
        
    def handle_help(self) -> bool:
        """显示帮助信息"""
        help_text = """
可用命令:
/quit - 退出程序
/stream - 切换流式输出模式
/debug - 切换调试模式
/multi - 切换多行输入模式
/help - 显示此帮助信息
"""
        print(ColorHandler.system_text(help_text))
        return True
        
    def handle_debug(self) -> bool:
        """切换调试模式"""
        from handler.debug_handler import DebugHandler
        DebugHandler.toggle_debug()
        print(ColorHandler.system_text(f"调试模式已{'开启' if DebugHandler.is_debug_enabled() else '关闭'}"))
        return True
        
    def handle_multi(self) -> bool:
        """处理多行输入命令"""
        if self.chat_handler:
            self.chat_handler.multi_mode = True
            print(ColorHandler.system_text("已进入多行输入模式"))
        return True
    
    def add_command(self, command_name: str, command_func):
        """
        添加自定义命令
        :param command_name: 命令名称
        :param command_func: 命令处理函数
        """
        self.commands[command_name.lower()] = command_func