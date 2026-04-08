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

# 启动 Streamlit 应用
# Railway 会注入 PORT，若本地运行则回退到 8501。
CMD ["sh", "-c", "streamlit run src/interface/app.py --server.address=0.0.0.0 --server.port=${PORT:-8501} --server.headless=true --server.enableCORS=false --server.maxMessageSize=200"]
