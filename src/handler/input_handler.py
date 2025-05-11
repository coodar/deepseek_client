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
        line_buffer = ""  # 用于存储当前行输入的字符
        byte_buffer = b""  # 用于处理多字节UTF-8字符
        while not self.stop_event.is_set():
            if sys.stdin.isatty():  # 确保在终端环境中运行
                try:
                    if os.name == 'nt':  # Windows
                        import msvcrt
                        if msvcrt.kbhit():
                            char_bytes = msvcrt.getch()
                            try:
                                char = char_bytes.decode('utf-8')
                                self.input_queue.put(char)
                                if char == '\r' or char == '\n':
                                    line_buffer = ""
                                elif char == '\x08': # Backspace for Windows
                                    # 确保在Windows环境下也正确处理退格键
                                    if line_buffer:
                                        line_buffer = line_buffer[:-1]
                                        self.input_queue.put('<BACKSPACE>')
                                        DebugHandler.debug(f"Windows退格后的行缓冲区: '{line_buffer}'")
                                else:
                                    line_buffer += char
                            except UnicodeDecodeError:
                                # Handle potential decoding errors if necessary
                                pass 
                    else:  # Unix/Linux/MacOS
                        import select
                        import termios
                        import tty
                        old_settings = termios.tcgetattr(sys.stdin)
                        try:
                            tty.setraw(sys.stdin.fileno(), termios.TCSANOW)
                            if select.select([sys.stdin], [], [], 0)[0]:
                                raw_byte = os.read(sys.stdin.fileno(), 1)
                                if raw_byte == b'\x7f' or raw_byte == b'\b':  # 退格 (DEL or Backspace)
                                    # 处理Unicode字符退格
                                    if line_buffer:                                        
                                        # 直接使用Python字符串切片删除最后一个字符
                                        line_buffer = line_buffer[:-1]
                                        self.input_queue.put('<BACKSPACE>')
                                        byte_buffer = b""  # 清空字节缓冲区
                                        # 强制刷新输入队列和缓冲区
                                        self.input_queue.queue.clear()
                                        
                                elif raw_byte == b'\r' or raw_byte == b'\n': # Enter
                                    self.input_queue.put(raw_byte.decode('utf-8', errors='ignore'))
                                    line_buffer = ""
                                    byte_buffer = b""
                                    # Restore terminal settings immediately after Enter for some terminals
                                    # termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                                    # tty.setraw(sys.stdin.fileno(), termios.TCSANOW)
                                else:
                                    byte_buffer += raw_byte
                                    try:
                                        # Try to decode the byte buffer
                                        decoded_char = byte_buffer.decode('utf-8')
                                        # If successful, it's a complete character (or multiple)
                                        for char_part in decoded_char:
                                            self.input_queue.put(char_part)
                                            line_buffer += char_part
                                        byte_buffer = b""  # Clear buffer after successful decode
                                    except UnicodeDecodeError:
                                        # Not enough bytes for a complete character, wait for more
                                        if len(byte_buffer) > 4: # Avoid infinitely growing buffer for invalid sequences
                                            byte_buffer = b"" # Reset if too long and still undecodable
                                        pass
                        finally:
                            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                            time.sleep(0.0001) # 将轮询间隔缩短至0.1ms
                            # 强制刷新输出缓冲区
                            sys.stdout.flush()
                            os.fsync(sys.stdout.fileno())
                            # 清空输入缓冲区残留数据
                            if os.name != 'nt':
                                termios.tcflush(sys.stdin, termios.TCIFLUSH)
                except Exception as e:
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
