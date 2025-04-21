import sys
from pathlib import Path

# 添加项目根目录到Python路径
from handler.chat_handler import ChatHandler
from handler.command_handler import CommandHandler
from handler.color_handler import ColorHandler
from api.deepseek_api import DeepSeekAPI
from config.setting import DEFAULT_MODEL, DEFAULT_TEMPERATURE
from handler.command_handler import CommandHandler
from handler.debug_handler import DebugHandler
from handler.color_handler import ColorHandler

class DeepSeekCLI:
    def __init__(self):
        """初始化DeepSeek CLI客户端"""
        self.dialog_handler = ChatHandler()
        self.command_handler = CommandHandler(chat_handler=self.dialog_handler)
    
    def run(self):
        """运行CLI交互循环"""
        DebugHandler.debug(f"DeepSeekCLI 初始化完成，模型: {DEFAULT_MODEL}, 温度: {DEFAULT_TEMPERATURE}")
        print(ColorHandler.system_text("=== DeepSeek CLI 帮助信息 ==="))
        print(ColorHandler.system_text("可用命令:"))
        print(ColorHandler.system_text("  /help   - 显示详细帮助信息"))
        print(ColorHandler.system_text("  /quit   - 退出交互"))
        print(ColorHandler.system_text("  /stream - 切换流式输出模式（默认开启）"))
        print(ColorHandler.system_text("  /multi  - 进入多行输入模式（使用/eof结束输入）"))
        print(ColorHandler.system_text("  /model  - 切换AI模型（DeepSeek Chat/Reasoner）"))
        print(ColorHandler.system_text("  /reset  - 重置对话历史"))
        print(ColorHandler.system_text("  /debug  - 切换调试模式"))
        print(ColorHandler.system_text("==========================="))
        
        while True:
            # 处理多行输入模式
            if self.dialog_handler.multi_mode:
                lines = []
                # print(ColorHandler.system_text("多行输入模式 (输入/eof结束):"))
                while True:
                    line = input(ColorHandler.user_text("> "))
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
                user_input = input(ColorHandler.user_text(prompt))
            
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
                    print(ColorHandler.reasoning_text(f"推理过程：\n" + reasoning))
                    print(ColorHandler.assistant_text(f"\n最终回复：\n" + answer))
                else:
                    print(ColorHandler.assistant_text(f"助手：\n" + assistant_reply))
                DebugHandler.debug("分阶段输出完成")
                DebugHandler.debug("非流式模式回复完成")

def main():
    cli = DeepSeekCLI()
    cli.run()

if __name__ == "__main__":
    main()