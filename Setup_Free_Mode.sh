# 安装 ollama (需要 sudo 密码)
curl -fsSL https://ollama.com/install.sh | sh

# 启动 ollama 服务 (如果是 Linux)
systemctl start ollama

# 拉取大语言模型 (Chat) - 通义千问 7B (中文能力强)
ollama pull qwen2.5:7b

# 拉取嵌入模型 (Embeddings) - Nomic Embed Text (专用于 RAG，体积小效果好)
ollama pull nomic-embed-text

# 运行智能体
python src/main.py
