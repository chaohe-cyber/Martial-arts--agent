#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ok=true

echo "[1/5] Python 版本"
python --version || ok=false

echo "[2/5] 关键依赖检查"
python - <<'PY' || ok=false
mods = ["streamlit", "pandas", "langchain", "langchain_ollama", "chromadb"]
missing = []
for m in mods:
    try:
        __import__(m)
    except Exception:
        missing.append(m)
if missing:
    raise SystemExit(f"缺少依赖: {', '.join(missing)}")
print("依赖检查通过")
PY

echo "[3/5] Ollama 可执行文件"
if ! command -v ollama >/dev/null 2>&1; then
  echo "未找到 ollama 命令"
  ok=false
else
  ollama --version || ok=false
fi

echo "[4/5] Ollama 服务状态"
if command -v curl >/dev/null 2>&1; then
  if ! curl -sS http://127.0.0.1:11434/api/tags >/dev/null; then
    echo "Ollama 服务未就绪 (127.0.0.1:11434)"
    ok=false
  else
    echo "Ollama 服务可访问"
  fi
fi

echo "[5/5] 模型检查"
if command -v ollama >/dev/null 2>&1; then
  models="$(ollama list || true)"
  echo "$models" | grep -q "qwen2.5:1.5b" || { echo "缺少模型 qwen2.5:1.5b"; ok=false; }
  echo "$models" | grep -q "nomic-embed-text" || { echo "缺少模型 nomic-embed-text"; ok=false; }
fi

if [ "$ok" = true ]; then
  echo "健康检查通过"
  exit 0
else
  echo "健康检查未通过，请按 README 排查"
  exit 1
fi
