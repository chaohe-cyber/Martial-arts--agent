# 武术教学智能体 Martial Arts Teaching Agent

融合领域知识与大语言模型的武术教学智能体，面向传统体育教学、课程辅导和教学研究场景。

项目目标：

- 用 RAG 让回答更贴近武术教材与规范。
- 用本地模型降低成本并保护数据隐私。
- 用 Web 界面降低使用门槛，支持课堂演示与公开体验。

## 亮点

- 领域知识增强：支持 txt 与 xlsx 资料入库检索。
- 本地免费推理：支持 Ollama，本地可运行。
- 双入口使用：CLI 和 Streamlit Web 均可用。
- 可扩展架构：已预留动作评估与研究评估模块扩展位。

## 系统架构

```mermaid
graph TD
    User[用户] --> |提问/上传资料| Interface[交互界面 Web/CLI]
    Interface --> Controller[核心控制器]

    subgraph Agent[智能体核心]
        Controller --> RAG[检索增强生成]
        Controller --> Eval[教学评估模块]
        RAG --> KB[(武术知识库)]
        KB --> VDB[向量数据库]
        RAG --> LLM[本地或云端大模型]
    end

    LLM --> Controller
    Controller --> User
```

## 目录结构

- src: 核心代码
- data/knowledge_base: 武术知识资料
- docs: 文档与发布说明
- scripts: 辅助脚本
- tests: 测试目录

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动本地模型服务

```bash
ollama pull qwen2.5:1.5b
ollama pull nomic-embed-text
```

### 3. 启动命令行模式

```bash
python src/main.py
```

首次建议输入 index 建立索引，随后再提问。

### 4. 启动 Web 演示界面

```bash
streamlit run src/interface/app.py
```

## 面向公开演示

- 局域网演示：streamlit run src/interface/app.py --server.address 0.0.0.0
- 公网临时分享：可使用 start_public.sh

## 开源协作

- 贡献指南：[CONTRIBUTING.md](CONTRIBUTING.md)
- 大文件建议：[docs/LARGE_FILES.md](docs/LARGE_FILES.md)
- GitHub 发布流程：[docs/GITHUB_RELEASE_GUIDE.md](docs/GITHUB_RELEASE_GUIDE.md)

## 当前路线图

- 增加动作识别模块接入
- 增加评测数据记录与可视化
- 增加自动化测试与基线评测脚本

## 许可证

本项目采用 MIT License，见 [LICENSE](LICENSE)。
