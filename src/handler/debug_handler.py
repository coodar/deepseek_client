"""调试处理模块，用于控制调试输出"""

class DebugHandler:
    _debug_mode = False
    
    @classmethod
    def is_debug_mode(cls) -> bool:
        """获取当前调试模式状态
        :return: 是否处于调试模式
        """
        return cls._debug_mode
    
    @classmethod
    def set_debug_mode(cls, enabled: bool) -> None:
        """设置调试模式状态
        :param enabled: 是否启用调试模式
        """
        cls._debug_mode = enabled
    
    @classmethod
    def debug(cls, message: str) -> None:
        """输出调试信息，仅在调试模式下有效
        :param message: 调试信息
        """
        if cls._debug_mode:
            print(f"[DEBUG] {message}")