# 武术智能体开源到 GitHub 的详细步骤

下面这份指南默认你已经在项目目录：`/home/chenchaohe/Desktop/martial-arts-agent`

## 0. 先理解整个流程

把项目开源到 GitHub，本质上就是 4 件事：

1. 让本地文件变成一个 Git 仓库
2. 把你想公开的代码提交到本地仓库
3. 在 GitHub 网站上创建一个公开仓库
4. 把本地仓库推送到 GitHub

你可以把它理解成：
- 本地电脑 = 你写好的稿子
- Git = 记录稿子版本的工具
- GitHub = 放到网上公开展示的平台

---

## 1. 准备 Git 环境

先打开终端，进入项目目录：

```bash
cd /home/chenchaohe/Desktop/martial-arts-agent
```

如果你还没安装 Git，需要先安装它。但大多数 Linux 系统都已经装好了。你可以先检查：

```bash
git --version
```

如果能看到版本号，说明 Git 可以用。

---

## 2. 初始化本地仓库

如果这个项目还不是 Git 仓库，先初始化：

```bash
git init
```

然后把默认分支改成 `main`，这是 GitHub 现在最常用的分支名：

```bash
git branch -M main
```

执行完以后，项目目录里会多一个 `.git/` 文件夹，这表示 Git 已经开始管理这个项目了。

---

## 3. 配置你的身份信息

Git 提交时需要知道是谁提交的。只要设置一次就行。

### 全局设置（推荐）

```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
```

例如：

```bash
git config --global user.name "Chen Chaohe"
git config --global user.email "chen@example.com"
```

### 只对当前项目设置

如果你不想影响其他项目，可以只对当前仓库设置：

```bash
git config user.name "你的名字"
git config user.email "你的邮箱"
```

### 检查是否设置成功

```bash
git config --get user.name
git config --get user.email
```

---

## 4. 确认哪些文件会被提交

先查看仓库状态：

```bash
git status
```

你会看到很多 `untracked files`，这是正常的，表示这些文件还没提交。

你这个项目已经有 `.gitignore`，它会自动忽略一些不该公开的内容，比如：
- `.env`
- `__pycache__/`
- `data/chroma_db/`
- `streamlit.log`

这一步非常重要，因为你不应该把密钥、缓存、数据库索引这些东西上传到 GitHub。

---

## 5. 添加文件并提交第一次版本

把当前项目文件加入 Git：

```bash
git add .
```

然后做第一次提交：

```bash
git commit -m "Initial commit: martial arts teaching agent"
```

如果这里报错，通常是这几种原因：

1. 没设置 `user.name` 和 `user.email`
2. 终端里有文件权限问题
3. 你在错误的目录里执行了命令

如果提交成功，说明你的本地仓库已经准备好了。

---

## 6. 在 GitHub 网站上创建仓库

接下来去 GitHub 网站：

1. 打开 https://github.com
2. 登录你的账号
3. 点击右上角 `+`
4. 选择 `New repository`
5. 填写仓库名，例如：`martial-arts-agent`
6. 选择 `Public`
7. **不要**勾选：
   - Add a README file
   - Add .gitignore
   - Choose a license

为什么不要勾选？因为你本地已经有这些文件了，如果 GitHub 也帮你建一份，后面会产生冲突。

创建完成后，GitHub 会给你一个地址，类似这样：

```bash
https://github.com/你的用户名/martial-arts-agent.git
```

把它复制下来，等会儿要用。

---

## 7. 把本地仓库连接到 GitHub

在终端输入：

```bash
git remote add origin https://github.com/你的用户名/martial-arts-agent.git
```

如果你之前已经加过远程地址，可以先删掉旧的：

```bash
git remote remove origin
git remote add origin https://github.com/你的用户名/martial-arts-agent.git
```

然后检查一下是否配置成功：

```bash
git remote -v
```

如果看到 `fetch` 和 `push` 都指向你的 GitHub 地址，说明连接好了。

---

## 8. 推送到 GitHub

把本地代码推送到 GitHub：

```bash
git push -u origin main
```

第一次推送时，GitHub 可能会让你登录：
- 如果是网页方式，就按提示登录
- 如果是命令行方式，可能需要输入 Personal Access Token（PAT），不是你的 GitHub 密码

如果你没有 Token，可以在 GitHub 的设置里创建：
- GitHub → Settings
- Developer settings
- Personal access tokens
- 生成一个有仓库权限的 token

---

## 9. 验证是否发布成功

推送完成后，刷新 GitHub 仓库页面，你应该能看到：

- `README.md`
- `LICENSE`
- `src/`
- `data/`
- `requirements.txt`

如果这些都能看到，说明你的项目已经成功公开了。

---

## 10. 后续更新代码时怎么做

以后你改了代码，不需要重新初始化仓库，只要继续这三步：

```bash
git add .
git commit -m "Describe your change"
git push
```

例如：

```bash
git add .
git commit -m "Add public web demo"
git push
```

---

## 11. 开源前检查清单

发布前建议你确认这些事情：

- `.env` 没有上传
- API Key 没写进 README
- `data/chroma_db/` 这种本地索引没上传
- README 里有启动命令
- 说明了 Ollama 模型下载命令
- 说明了 Web 界面怎么启动

---

## 12. 适合你的最短命令清单

如果你不想看解释，只想直接执行，按这个顺序来：

```bash
cd /home/chenchaohe/Desktop/martial-arts-agent
git init
git branch -M main
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
git add .
git commit -m "Initial commit: martial arts teaching agent"
git remote add origin https://github.com/你的用户名/martial-arts-agent.git
git push -u origin main
```

---

## 13. 如果你卡住了

常见问题：

### 问题 A：`fatal: not a git repository`
说明你没有进入项目目录。先运行：

```bash
cd /home/chenchaohe/Desktop/martial-arts-agent
```

### 问题 B：`Please tell me who you are`
说明你还没设置用户名和邮箱。先运行：

```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
```

### 问题 C：`repository not found`
说明远程地址写错了，或者 GitHub 仓库还没创建。

### 问题 D：`Authentication failed`
说明你需要用 GitHub Token，而不是密码。

---

如果你愿意，我下一步可以直接帮你把 README 再整理成更适合公开发布的版本，并补上 GitHub 仓库首页应该展示的内容。
