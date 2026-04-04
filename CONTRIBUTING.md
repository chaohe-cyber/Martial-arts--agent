# Contributing Guide

感谢你关注这个项目。

## 开发环境

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 启动本地模型

```bash
ollama pull qwen2.5:1.5b
ollama pull nomic-embed-text
```

## 分支策略

- main: 稳定分支
- feature/*: 新功能分支
- fix/*: 修复分支

## 提交规范

推荐格式：

- feat: 新功能
- fix: 问题修复
- docs: 文档更新
- refactor: 重构
- chore: 工程维护

示例：

```text
feat: add streaming response in web ui
fix: handle missing ollama model gracefully
docs: improve user onboarding documentation
```

## Pull Request 要求

- 描述变更目的与影响范围
- 给出复现步骤或验证方法
- 涉及 UI 变更时附截图
- 不要提交密钥和本地缓存

## 安全与隐私

- 禁止提交 .env
- 禁止提交真实 API Key
- 大文件优先采用 LFS 管理
