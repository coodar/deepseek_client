from .chat_handler import ChatHandler
from .setting import API_KEY, DEFAULT_MODEL, DEFAULT_TEMPERATURE

def main():
    """
    DeepSeek API命令行接口主函数
    """
    # 初始化对话处理器
    dialog_handler = ChatHandler(
        api_key=API_KEY,
        model=DEFAULT_MODEL,
        temperature=DEFAULT_TEMPERATURE
    )
    
    print("DeepSeek API客户端已初始化，模型:", DEFAULT_MODEL)
    print("输入'quit'退出交互")
    
    while True:
        user_input = input("用户: ")
        if user_input.lower() == 'quit':
            break
            
        dialog_handler.add_user_message(user_input)
        assistant_reply = dialog_handler.get_assistant_reply()
        print("助手:", assistant_reply)

if __name__ == "__main__":
    main()