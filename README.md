# 武术教学智能体 Martial Arts Teaching Agent

[中文说明](README.md) | [English](README_EN.md)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey)

面向传统体育教学与研究场景的武术教学系统，融合武术领域知识检索与对话交互能力。

作者单位：武汉体育学院武术学院汤立许教授团队。

项目目标：

- 用 RAG 让回答更贴近武术教材与规范。
- 用本地模型降低成本并保护数据隐私。
- 用 Web 界面降低使用门槛，支持课堂演示与公开体验。

## 最新更新（2026-04）

- 数字人互动升级：支持服务端真实语音播报（edge-tts），避免浏览器语音权限不稳定问题。
- 文字驱动动作演示：可从一段长文本中识别动作顺序，联动动作步骤、常见错误与纠正提示。
- 动作与语音同步：在数字人页面可进行“播报音频 + 动作演示”同步播放。
- 多模态能力完善：支持上传视频动作分析、摄像头实时检测与课堂评分建议。
- 部署能力增强：新增 Docker 与 docker-compose 部署文件，可接入 Railway 自动部署。

## 项目特点

- 领域知识增强：支持 txt 与 xlsx 资料入库检索。
- 本地推理部署：支持 Ollama，降低外部依赖。
- 双入口使用：CLI 和 Streamlit Web 均可用。
- 数字人教学交互：支持播报稿整理、真实音频生成与下载。
- 文字动作教学：支持多动作序列解析与教学纠错提示。
- 可扩展架构：已预留动作评估与研究评估模块扩展位。

## 系统架构

![武术智能体系统总览](docs/figures/system_overview_zh.svg)

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

## 知识库处理流程图

![武术知识库处理流程](docs/figures/knowledge_pipeline_zh.svg)

## 武术智能体 Web 界面剖面图

![武术智能体 Web 界面剖面图](docs/figures/web_section_zh.svg)

## 课堂演示流程图

![武术智能体课堂演示流程](docs/figures/classroom_demo_flow_zh.svg)

## 目录结构

- src: 核心代码
- data/knowledge_base: 武术知识资料
- docs: 项目文档
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
./scripts/run_cli.sh
```

首次建议输入 index 建立索引，随后再提问。

### 4. 启动 Web 演示界面

```bash
./scripts/run_web.sh
```

### 5. 环境健康检查

```bash
./scripts/health_check.sh
```

### 6. Docker 启动（可选）

```bash
docker-compose up --build
```

## 面向公开演示

- 局域网演示：streamlit run src/interface/app.py --server.address 0.0.0.0
- 公网临时分享：可使用 start_public.sh
- 长期稳定链接：推荐使用 Railway（连接 GitHub 后可自动部署）

详细部署说明见：[DEPLOYMENT.md](DEPLOYMENT.md)

## Demo 建议

- 课堂场景：先运行 `./scripts/health_check.sh`，确认环境正常。
- 讲解场景：使用 `./scripts/run_web.sh` 打开 Web 页面进行现场提问。
- 研究场景：在 `data/knowledge_base` 放入课程资料后，先重建索引再演示问答。

## 开源协作

- 贡献指南：[CONTRIBUTING.md](CONTRIBUTING.md)
- 大文件建议：[docs/LARGE_FILES.md](docs/LARGE_FILES.md)
- Issue 模板：[.github/ISSUE_TEMPLATE](.github/ISSUE_TEMPLATE)
- PR 模板：[.github/pull_request_template.md](.github/pull_request_template.md)

## 当前路线图

- 增加动作识别骨架点精度评估与更细粒度评分
- 增加课堂报告导出（PDF/图片）
- 增加自动化端到端测试与部署后健康巡检

## 常见问题 FAQ

### 1. 回答速度慢怎么办？

先执行 `ollama pull qwen2.5:1.5b`，并确认本地已使用该模型。

### 2. 知识库更新后为什么回答没变化？

需要重新建立索引，Web 端点击“重新索引”，或在 CLI 中输入 `index`。

### 3. 推送仓库时出现大文件警告怎么办？

参考 [docs/LARGE_FILES.md](docs/LARGE_FILES.md)，建议使用 Git LFS 管理 `.xlsx`。

## 许可证

本项目采用 MIT License，见 [LICENSE](LICENSE)。
