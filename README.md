# 武术教学智能体 (Martial Arts Teaching Agent)

本项目旨在复现并实现《生成式AI赋能传统体育教学：融合领域知识与大语言模型的武术教学智能体开发与效能评估的研究》中的核心理念。通过融合传统的武术领域知识（动作规范、心法、历史）与先进的大语言模型（LLM），构建一个能够提供个性化指导、动作解析及文化传承的智能体。

## 核心功能

1.  **领域知识增强 (RAG)**:
    *   集成武术教材、动作图解、视频元数据。
    *   使用向量数据库进行知识检索，确保回答的专业性和准确性。

2.  **多模态交互**:
    *   **文本/语音**: 解答关于武术理论、历史、训练计划的问题。
    *   **视觉 (计划中)**: 结合姿态估计 (Pose Estimation) 技术，对用户的练习动作进行评分和纠错。

3.  **个性化教学**:
    *   根据用户的水平（初学者、进阶）调整教学内容的深度和难度。
    *   生成定制化的训练计划。

## 系统架构

```mermaid
graph TD
    User[用户] --> |提问/上传视频| Interface[交互界面 (Web/App)]
    Interface --> Controller[核心控制器]
    
    subgraph "智能体核心 (Agent Core)"
        Controller --> Intent[意图识别]
        Intent --> |理论询问| RAG[检索增强生成]
        Intent --> |动作指导| Vision[视觉分析模块]
        
        RAG --> KnowledgeBase[(武术知识库)]
        KnowledgeBase --> VectorDB[向量数据库]
        
        Vision --> PoseModel[姿态评估模型]
        
        RAG & Vision --> LLM[大语言模型 (Generator)]
    end
    
    LLM --> |生成反馈| Controller
    Controller --> |回答/纠错建议| User
```

## 目录结构

*   `src/`: 源代码
    *   `agent/`: 智能体核心逻辑
    *   `knowledge/`: 知识库管理与检索引擎
    *   `vision/`: (预留) 视觉分析模块
    *   `interface/`: 用户界面 (Streamlit/FastAPI)
*   `data/`: 数据文件
    *   `knowledge_base/`: 原始文档与处理后的数据
*   `docs/`: 文档
*   `tests/`: 测试用例

## 快速开始

1.  安装依赖: `pip install -r requirements.txt`
2.  配置环境变量: `.env` (API Key等)
3.  运行: `python src/main.py`

## 发布到 GitHub

如果你想把这个项目开源到 GitHub，请先阅读 [GitHub 发布指南](docs/GITHUB_RELEASE_GUIDE.md)。

最短流程如下：

1.  `git init`
2.  `git add .`
3.  `git commit -m "Initial commit: martial arts teaching agent"`
4.  在 GitHub 创建一个公开仓库
5.  `git remote add origin https://github.com/你的用户名/仓库名.git`
6.  `git push -u origin main`
