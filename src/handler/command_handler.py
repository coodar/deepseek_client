"""
命令处理模块，专门处理用户输入的命令
"""
import json
from typing import List, Dict

# 尝试兼容包模式和开发模式的导入
try:
    # 包模式导入
    from handler.debug_handler import DebugHandler
    from handler.color_handler import ColorHandler
except ImportError:
    # 开发模式导入
    import sys
    from pathlib import Path
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    from src.handler.debug_handler import DebugHandler
    from src.handler.color_handler import ColorHandler

DebugHandler.debug(f"json模块已导入，版本: {json.__version__}")

class CommandHandler:
    def __init__(self, chat_handler=None):
        self.chat_handler = chat_handler
        self.commands = {
            '/quit': self.handle_quit,
            '/stream': self.handle_stream_mode,
            '/help': self.handle_help,
            '/debug': self.handle_debug,
            '/multi': self.handle_multi,
            '/model': self.handle_model,
            '/reset': self.handle_reset,
            '/stop': self.handle_interrupt
        }
        self.stream_mode = True
    
    def handle_command(self, user_input: str) -> bool:
        """
        处理用户输入的命令
        :param user_input: 用户输入
        :return: 是否继续对话，None表示命令已处理但继续对话，False表示退出，True表示非命令
        """
        # 严格检查输入是否以斜杠开头
        normalized_input = user_input.lower().strip()
        DebugHandler.debug(f"处理用户输入，原始输入: '{user_input}', 标准化后: '{normalized_input}'")
        if not normalized_input.startswith('/'):
            return True
            
        # 优先处理本地命令
        command_func = self.commands.get(normalized_input)
        DebugHandler.debug(f"查找命令处理函数，命令: '{normalized_input}', 找到函数: {command_func}")
        if command_func:
            result = command_func()
            if not result:  # 如果命令处理返回false，阻止后续流程
                return False
            return None  # 返回None表示命令已处理但继续对话
            
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
        from config.setting import AVAILABLE_MODELS
        current_model = self.chat_handler.model if self.chat_handler else "deepseek-chat"
        model_display_name = AVAILABLE_MODELS.get(current_model, current_model)
        
        help_text = """
可用命令:
/quit - 退出程序
    说明: 结束当前会话并退出程序
    用法: 直接输入 /quit

/stream - 切换流式输出模式
    说明: 开启或关闭AI回复的流式输出
    用法: 直接输入 /stream
    当前状态: %s

/debug - 切换调试模式
    说明: 开启或关闭调试信息的显示
    用法: 直接输入 /debug
    当前状态: %s

/multi - 切换多行输入模式
    说明: 进入多行输入模式，可以输入多行文本
    用法: 输入 /multi 进入多行模式，输入内容后使用 /eof 结束输入

/model - 切换AI模型
    说明: 在可用模型之间切换
    用法: 输入 /model 然后输入数字或模型ID
    当前模型: %s

/reset - 重置对话历史
    说明: 清空当前的对话历史，开始一个全新的会话
    用法: 直接输入 /reset

/stop - 中断当前输出
    说明: 在流式输出过程中立即停止输出
    用法: 直接输入 /stop

/help - 显示此帮助信息
    说明: 显示所有可用命令的详细说明
    用法: 直接输入 /help
""" % ('开启' if self.stream_mode else '关闭', '开启' if DebugHandler.is_debug_enabled() else '关闭', model_display_name)
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
        
    def handle_model(self) -> bool:
        """切换模型"""
        from config.setting import AVAILABLE_MODELS
        if self.chat_handler:
            current_model = self.chat_handler.model
            print(ColorHandler.system_text(f"当前模型: {AVAILABLE_MODELS.get(current_model, current_model)}"))
            print(ColorHandler.system_text("可用模型:"))
            
            for index, (model_id, model_name) in enumerate(AVAILABLE_MODELS.items(), start=1):
                print(ColorHandler.system_text(f"  {index}. {model_name} ({model_id})"))
            
            print(ColorHandler.system_text("请输入数字或模型ID:"))
            model_input = input(ColorHandler.user_text("> ")).strip()
            
            selected_model = None
            if model_input.isdigit():
                index = int(model_input) - 1
                model_list = list(AVAILABLE_MODELS.keys())
                if 0 <= index < len(model_list):
                    selected_model = model_list[index]
                else:
                    print(ColorHandler.system_text(f"无效的数字选项: {model_input}"))
                    return True
            elif model_input in AVAILABLE_MODELS:
                selected_model = model_input
            else:
                print(ColorHandler.system_text(f"无效的模型ID或数字: {model_input}"))
                return True
            
            if selected_model and selected_model in AVAILABLE_MODELS:
                self.chat_handler.model = selected_model
            else:
                print(ColorHandler.system_text(f"无效的模型配置: {selected_model}"))
                return True
            print(ColorHandler.system_text(f"已切换到模型: {AVAILABLE_MODELS[selected_model]}"))
            print(ColorHandler.system_text("对话历史已保留，您可以继续之前的对话"))
        return True
        
    def handle_reset(self) -> bool:
        """重置对话历史"""
        if self.chat_handler:
            self.chat_handler.reset_conversation()
            print(ColorHandler.system_text("对话历史已重置，开始新的对话"))
        return True
        
    def handle_interrupt(self) -> bool:
        """中断当前输出"""
        if self.chat_handler:
            self.chat_handler.interrupt_output()
            print(ColorHandler.system_text("已发送中断信号"))
        return True
    
    def add_command(self, command_name: str, command_func):
        """
        添加自定义命令
        :param command_name: 命令名称
        :param command_func: 命令处理函数
        """
        self.commands[command_name.lower()] = command_func