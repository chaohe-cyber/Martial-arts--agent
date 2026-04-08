# 武术智能体 - 部署指南

## 🚀 快速部署方案

### 方案 1: Docker 本地部署（推荐）

#### 前置要求
- 已安装 Docker 和 Docker Compose

#### 部署步骤

```bash
# 1. 进入项目目录
cd martial-arts-agent

# 2. 构建并启动容器
docker-compose up --build

# 3. 访问应用
# 浏览器打开：http://localhost:8501
```

#### 停止应用
```bash
docker-compose down
```

---

### 方案 2: Railway 云部署（推荐，完全免费 + 公网访问）

#### 前置要求
- 一个 GitHub 账户
- 一个 Railway 账户（https://railway.app）

#### 部署步骤

1. **推送代码到 GitHub**
   ```bash
   git push origin main
   ```

2. **连接 Railway**
   - 访问 https://railway.app
   - 点击 "New Project" → "Deploy from GitHub"
   - 授权并选择 `martial-arts-agent` 仓库
   - Railway 会自动检测到 Dockerfile 并构建部署

3. **配置环境变量（如需）**
   - 在 Railway Dashboard 中进入项目
   - 点击 Settings → Variables
   - 建议至少添加以下变量（确保云端功能完整可用）：

   ```bash
   OPENAI_API_KEY=你的云端模型API密钥
   OPENAI_BASE_URL=你的OpenAI兼容网关地址(可选)
   OPENAI_MODEL=gpt-4o-mini
   OPENAI_EMBEDDING_MODEL=text-embedding-3-small
   ```

   - 若你使用本地/自建 Ollama 服务，可改用：
   ```bash
   OLLAMA_BASE_URL=http://你的ollama服务地址:11434
   OLLAMA_MODEL=qwen2.5:1.5b
   OLLAMA_EMBEDDING_MODEL=nomic-embed-text
   ```

4. **获取公网链接**
   - 部署完成后，Railway 会自动分配一个公网域名
   - 格式：`https://your-project-name.railway.app`
   - 这个链接可以稳定使用，无需额外续费

5. **端口说明（重要）**
   - Railway 会自动注入 `PORT` 环境变量
   - 本项目 Docker 启动命令已适配：优先监听 `PORT`，本地回退 `8501`

---

### 方案 3: Heroku 部署

> ⚠️ 注意：Heroku 免费层已停用，需要付费

---

### 方案 4: 自托管服务器部署

#### 使用 SSH 和 Git 部署到你的服务器

1. **在服务器上克隆仓库**
   ```bash
   git clone https://github.com/yourusername/martial-arts-agent.git
   cd martial-arts-agent
   ```

2. **使用 Docker Compose 启动**
   ```bash
   docker-compose up -d
   ```

3. **配置反向代理（Nginx）**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8501;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

4. **配置 HTTPS（使用 Let's Encrypt）**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

---

## 📊 部署方案对比

| 方案 | 成本 | 易用度 | 稳定性 | 公网访问 | 推荐场景 |
|------|------|--------|--------|---------|---------|
| Docker 本地 | 免费 | ⭐⭐⭐ | ⭐⭐⭐ | ❌ | 本地测试、内网部署 |
| **Railway** | **免费** | **⭐⭐⭐** | **⭐⭐⭐⭐⭐** | **✅** | **推荐首选** |
| Heroku | 付费 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ | 知名平台，但需付费 |
| 自托管服务器 | 付费 | ⭐⭐ | ⭐⭐⭐⭐ | ✅ | 完全控制、企业级 |

---

## 🔗 当前临时链接

- **公网临时链接**：https://08d960cc10c7fa.lhr.life
  - 由 `localhost.run` 提供，当本地服务运行时可用
  - 链接会在关闭服务后失效

- **本地链接**：http://localhost:8501
  - 仅在本地开发机器上访问

---

## 📝 环境变量配置（可选）

在 `docker-compose.yml` 或云平台中可添加：

```yaml
environment:
  - PYTHONUNBUFFERED=1
  - STREAMLIT_SERVER_HEADLESS=true
  - STREAMLIT_SERVER_MAXMESSAGESIZE=200
```

---

## 🆘 故障排除

### Docker 构建失败
```bash
# 清理缓存重新构建
docker-compose down
docker system prune -a
docker-compose up --build
```

### 端口被占用
```bash
# 使用其他端口
# 在 docker-compose.yml 中改为：
ports:
  - "8502:8501"
```

### 容器内报错
```bash
# 查看实时日志
docker-compose logs -f martial-arts-agent
```

### Railway 部署失败（常见）
1. **Healthcheck Failed / Service Unavailable**
   - 原因：应用没有监听 Railway 分配的 `PORT`
   - 处理：确认使用最新 Dockerfile（已支持 `--server.port=${PORT:-8501}`）

2. **Build Failed（依赖下载超时）**
   - 处理：在 Railway 里点击 `Redeploy` 重试
   - 若多次失败，可在低峰时段重试，或改为先本地构建验证

3. **部署成功但页面打不开**
   - 处理：确认 Service 已分配 Public Domain
   - 处理：查看 Deploy Logs，确认出现 `Network URL` / `Server started`

---

## 💡 推荐部署流程

1. **开发阶段**：使用 Docker 本地部署测试
2. **分享阶段**：推送到 GitHub，在 Railway 上部署获得公网链接
3. **长期运营**：考虑自托管服务器或企业级服务

---

需要帮助？请查阅各平台官方文档或联系技术支持。
