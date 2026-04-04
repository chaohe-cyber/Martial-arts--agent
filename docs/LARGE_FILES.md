# Large File Management

当前仓库包含较大的 xlsx 数据文件，GitHub 会给出警告。

## 现状说明

- GitHub 推荐单文件小于 50MB
- GitHub 硬限制单文件小于 100MB
- 当前有文件约 65.9MB，能推送但会影响体验

## 推荐方案：Git LFS

1. 安装 Git LFS

```bash
git lfs install
```

2. 跟踪大文件类型

```bash
git lfs track "*.xlsx"
```

3. 提交 LFS 配置

```bash
git add .gitattributes
git commit -m "chore: track xlsx files with git lfs"
```

## 对已入库大文件进行迁移（可选）

如果希望把历史中的 xlsx 都改为 LFS，可使用：

```bash
git lfs migrate import --include="*.xlsx"
```

注意：该命令会重写历史，需要与你的协作者确认后执行。

## 轻量替代方案

- 只保留样例数据在仓库
- 大型原始数据放到网盘或发布页下载
- 在 README 中给出下载入口
