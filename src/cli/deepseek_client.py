import sys
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
import readline
# 添加项目根目录到Python路径以兼容开发模式和包模式
try:
    # 尝试直接导入（包模式）
    from handler.chat_handler import ChatHandler
    from handler.command_handler import CommandHandler
    from handler.color_handler import ColorHandler
    from api.deepseek_api import DeepSeekAPI
    from config.setting import DEFAULT_MODEL, DEFAULT_TEMPERATURE
    from handler.debug_handler import DebugHandler
except ImportError:
    # 开发模式下调整导入路径
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent  # 获取项目根目录
    sys.path.insert(0, str(project_root))  # 将项目根目录添加到Python路径
    
    # 重新导入
    from src.handler.chat_handler import ChatHandler
    from src.handler.command_handler import CommandHandler
    from src.handler.color_handler import ColorHandler
    from src.api.deepseek_api import DeepSeekAPI
    from src.config.setting import DEFAULT_MODEL, DEFAULT_TEMPERATURE
    from src.handler.debug_handler import DebugHandler
    
    # 确保后续导入也能找到handler模块
    sys.path.insert(0, str(project_root / "src"))
# --- ASCII Art Definition ---
DEEPSEEK_CLIENT_ART = r"""
[medium_purple]
 ____                 ____            _       ____ _ _            _   
|  _ \  ___  ___ _ __/ ___|  ___  ___| | __  / ___| (_) ___ _ __ | |_ 
| | | |/ _ \/ _ \ '_ \___ \ / _ \/ _ \ |/ / | |   | | |/ _ \ '_ \| __|
| |_| |  __/  __/ |_) |__) |  __/  __/   <  | |___| | |  __/ | | | |_ 
|____/ \___|\___| .__/____/ \___|\___|_|\_\  \____|_|_|\___|_| |_|\__|
                |_|                                                   
[/medium_purple]
"""
# --- End ASCII Art ---
class DeepSeekCLI:
    def __init__(self):
        """初始化DeepSeek CLI客户端"""
        self.dialog_handler = ChatHandler()
        self.command_handler = CommandHandler(chat_handler=self.dialog_handler)
    
    def run(self):
        console = Console()
        console.clear()
        console.print(DEEPSEEK_CLIENT_ART)
        console.print(f"[bold green]DeepSeek Client 初始化完成，模型: {DEFAULT_MODEL}[/bold green]")
        """运行CLI交互循环"""
        DebugHandler.debug(f"DeepSeekCLI 初始化完成，模型: {DEFAULT_MODEL}, 温度: {DEFAULT_TEMPERATURE}")
        help_text = f"""
可用命令:
  [cyan]/help[/cyan]   - 显示详细帮助信息
  [cyan]/quit[/cyan]   - 退出交互
  [cyan]/stream[/cyan] - 切换流式输出模式（默认开启）
  [cyan]/multi[/cyan]  - 进入多行输入模式（使用/eof结束输入）
  [cyan]/model[/cyan]  - 切换AI模型（DeepSeek Chat/Reasoner）
  [cyan]/reset[/cyan]  - 重置对话历史
  [cyan]/stop[/cyan]   - 中断当前输出（也可使用Ctrl+S快捷键）
  [cyan]/debug[/cyan]  - 切换调试模式
"""
        console.print(Panel(help_text, title="帮助信息", border_style="blue", expand=False))
        
        while True:
            try:
                # 处理多行输入模式
                if self.dialog_handler.multi_mode:
                    lines = []
                    # print(ColorHandler.system_text("多行输入模式 (输入/eof结束):"))
                    while True:
                        line = console.input("[cyan]You > [/cyan]")
                        if line.strip() == "/eof":  # 使用/eof结束输入
                            break
                        lines.append(line)
                    
                    if not lines:  # 如果没有输入任何内容，继续下一轮
                        continue
                        
                    user_input = "\n".join(lines)
                    print(ColorHandler.system_text(f"已收到{len(lines)}行输入"))
                    self.dialog_handler.multi_mode = False  # 自动退出多行模式
                else:
                    prompt = f'[{self.dialog_handler.model}][{"流式" if self.command_handler.stream_mode else "非流式"}] > '
                    user_input = input(prompt)
                
                DebugHandler.debug(f"用户输入: {user_input}")
                
                # 特殊处理/multi命令
                if user_input.lower().strip() == '/multi':
                    self.dialog_handler.handle_multi()
                    continue
                    
                # 处理命令，如果返回False则退出，如果返回None则表示命令已处理但继续对话
                command_result = self.command_handler.handle_command(user_input)
                if command_result is False:
                    DebugHandler.debug("收到退出命令，终止循环")
                    break
                elif command_result is None:
                    DebugHandler.debug("命令已处理，跳过API调用")
                    continue
                    
                # 只有当命令未被处理时，才发送到API
                DebugHandler.debug("添加用户消息到对话历史")
                self.dialog_handler.add_user_message(user_input)
                
                DebugHandler.debug(f"获取助手回复 (流式模式: {self.command_handler.stream_mode})")
                assistant_reply = self.dialog_handler.get_assistant_reply(stream=self.command_handler.stream_mode)
                
                if not self.command_handler.stream_mode:
                    if '最终回复：' in assistant_reply:
                        reasoning, answer = assistant_reply.split('最终回复：', 1)
                        console.print("推理过程:")
                        console.print(Markdown(ColorHandler.reasoning_text(reasoning)))
                        console.print("最终回复:")
                        console.print(Markdown(ColorHandler.assistant_text(answer)))
                    else:
                        console.print("助手:")
                        console.print(Markdown(ColorHandler.assistant_text(assistant_reply)))
                    DebugHandler.debug("分阶段输出完成")
                    DebugHandler.debug("非流式模式回复完成")
            except KeyboardInterrupt:
                console.print("\n[yellow]Session interrupted. Exiting.[/yellow]")
                break
def main():
    cli = DeepSeekCLI()
    cli.run()

if __name__ == "__main__":
    main()