# DeepSeek Chat

一个用于与DeepSeek API交互的Python包

## 安装

```bash
pip install -e .
```

## 使用

```python
dscli
or 
cd /path/to/deepseek_chat 
python3 src/cli/deepseek_client.py
```

## 功能

- 与DeepSeek API交互
- 支持流式和非流式响应
- 错误处理和重试机制

## 环境变量配置

请按以下方式设置API密钥：

```bash
# 临时设置（当前终端会话有效）
export DEEPSEEK_API_KEY="your-api-key-here"

# 永久设置（添加到shell配置文件）
echo 'export DEEPSEEK_API_KEY="your-api-key-here"' >> ~/.bashrc
```