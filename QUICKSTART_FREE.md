# 武术教学智能体 - 免费版快速启动指南 (Linux)

本指南将教您如何使用完全免费的本地模型 (Ollama) 运行本项目，无需支付 OpenAI API 费用。

## 1. 安装 Ollama (AI模型运行环境)

打开终端，运行以下命令安装 Ollama：

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

安装完成后，启动服务（如果尚未运行）：
```bash
sudo systemctl start ollama
```

## 2. 下载 AI 模型

我们需要下载两个模型：一个用于对话（通义千问），一个用于理解知识库（Nomic Embeddings）。

```bash
#下载对话模型 (通义千问 7B - 中文能力强)
ollama pull qwen2.5:7b

# 下载嵌入模型 (用于知识库检索)
ollama pull nomic-embed-text
```

## 3. 准备项目环境

确保您在项目根目录 `martial-arts-agent` 下：

```bash
# 1. (可选) 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装 Python 依赖
pip install -r requirements.txt
```

## 4. 运行智能体

### 命令行版 (CLI)
```bash
python src/main.py
```
*   进入后输入 `index` 来加载您的太极拳知识库。
*   然后直接提问。

### 网页版 (GUI)
```bash
streamlit run src/interface/app.py
```

## 常见问题

*   **报错 "Connection refused"**: 检查 Ollama 是否正在运行 (`systemctl status ollama`)。
*   **显存不足**: 7B 模型大约需要 4GB+ 显存。如果没有显卡，Ollama 会自动使用 CPU（速度稍慢但可用）。
