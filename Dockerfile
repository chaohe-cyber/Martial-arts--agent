# 使用官方 Python 运行时作为基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建数据目录
RUN mkdir -p /app/data/chroma_db /app/data/knowledge_base

# 暴露端口 8501（Streamlit 默认端口）
EXPOSE 8501

# 设置 Streamlit 配置
RUN mkdir -p ~/.streamlit && \
    echo "[server]\n\
headless = true\n\
port = 8501\n\
enableCORS = false\n\
maxMessageSize = 200" > ~/.streamlit/config.toml

# 启动 Streamlit 应用
CMD ["streamlit", "run", "src/interface/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
