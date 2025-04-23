"""输入处理模块，提供非阻塞输入检测功能"""
import sys
import os
import threading
import queue
import time

# 尝试兼容包模式和开发模式的导入
try:
    # 包模式导入
    from handler.debug_handler import DebugHandler
except ImportError:
    # 开发模式导入
    import sys
    from pathlib import Path
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    from src.handler.debug_handler import DebugHandler

class InputHandler:
    """非阻塞输入处理器，用于在流式输出过程中检测用户输入"""
    
    def __init__(self):
        """初始化输入处理器"""
        self.input_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.input_thread = None
    
    def _input_worker(self):
        """输入线程工作函数，持续监听用户输入"""
        DebugHandler.debug("输入监听线程已启动")
        while not self.stop_event.is_set():
            if sys.stdin.isatty():  # 确保在终端环境中运行
                try:
                    # 使用非阻塞方式检查是否有输入
                    if os.name == 'nt':  # Windows
                        import msvcrt
                        if msvcrt.kbhit():
                            char = msvcrt.getch().decode('utf-8')
                            self.input_queue.put(char)
                    else:  # Unix/Linux/MacOS
                        import select
                        import termios
                        import tty
                        
                        # 保存终端设置
                        old_settings = termios.tcgetattr(sys.stdin)
                        try:
                            # 设置终端为raw模式，但不回显输入字符
                            tty.setraw(sys.stdin.fileno(), termios.TCSANOW)
                            
                            # 检查是否有输入可读取
                            if select.select([sys.stdin], [], [], 0)[0]:
                                char = sys.stdin.read(1)
                                # 将字符放入队列，但不回显
                                self.input_queue.put(char)
                                # 不再打印回车，避免干扰输出
                                if char == '\r' or char == '\n':
                                    # 只恢复和设置终端模式，不打印任何内容
                                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                                    # 重新设置raw模式
                                    tty.setraw(sys.stdin.fileno(), termios.TCSANOW)
                        finally:
                            # 恢复终端设置
                            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                except Exception as e:
                    DebugHandler.debug(f"输入检测异常: {str(e)}")
            time.sleep(0.1)  # 短暂休眠以减少CPU使用
        DebugHandler.debug("输入监听线程已停止")
    
    def start_listening(self):
        """开始监听用户输入"""
        if self.input_thread is None or not self.input_thread.is_alive():
            self.stop_event.clear()
            self.input_thread = threading.Thread(target=self._input_worker, daemon=True)
            self.input_thread.start()
            DebugHandler.debug("已启动输入监听")
    
    def stop_listening(self):
        """停止监听用户输入"""
        if self.input_thread and self.input_thread.is_alive():
            self.stop_event.set()
            self.input_thread.join(timeout=1.0)
            
            # 确保终端设置恢复正常
            if sys.stdin.isatty() and os.name != 'nt':
                try:
                    import termios
                    # 重置终端设置为规范模式
                    termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, termios.tcgetattr(sys.stdin))
                except Exception as e:
                    DebugHandler.debug(f"恢复终端设置时出错: {str(e)}")
            
            DebugHandler.debug("已停止输入监听")
    
    def check_for_stop_command(self):
        """检查是否接收到停止命令
        返回: 如果接收到/stop命令则返回True，否则返回False
        """
        command_buffer = ""
        
        # 检查队列中是否有输入
        while not self.input_queue.empty():
            try:
                char = self.input_queue.get_nowait()
                
                # 如果收到回车，检查当前缓冲区
                if char == '\n' or char == '\r':
                    if command_buffer.strip().lower() == "/stop":
                        DebugHandler.debug("检测到/stop命令")
                        # 清空队列
                        while not self.input_queue.empty():
                            self.input_queue.get_nowait()
                        return True
                    command_buffer = ""  # 重置缓冲区
                # 如果是Ctrl+C (ASCII值为3)或Ctrl+S (ASCII值为19)，也视为中断命令
                elif ord(char) == 3:
                    DebugHandler.debug("检测到Ctrl+C，视为中断命令")
                    return True
                elif ord(char) == 19:
                    DebugHandler.debug("检测到Ctrl+S，视为中断命令")
                    return True
                else:
                    command_buffer += char
                    
                    # 即时检查，如果已经输入了"/stop"，立即响应
                    if command_buffer.strip().lower() == "/stop":
                        DebugHandler.debug("检测到/stop命令（无需回车）")
                        # 清空队列
                        while not self.input_queue.empty():
                            self.input_queue.get_nowait()
                        return True
            except queue.Empty:
                break
        
        return False