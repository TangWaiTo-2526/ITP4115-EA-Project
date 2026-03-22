#!/usr/bin/env bash
# Codespace / devcontainer 建立後自動執行：啟動 Docker 資料庫、安裝 Python 依賴
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[post-create] workspace: $ROOT"

echo "[post-create] docker compose up (PostgreSQL + pgAdmin)..."
if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    docker compose up -d || echo "[post-create] 警告: docker compose up 失敗，可稍後手動執行: docker compose up -d" >&2
  else
    echo "[post-create] 警告: Docker daemon 尚未就緒，請稍後執行: docker compose up -d" >&2
  fi
else
  echo "[post-create] 警告: 未找到 docker 命令" >&2
fi

echo "[post-create] pip install -r requirements.txt ..."
python3 -m pip install -U pip setuptools wheel
python3 -m pip install -r requirements.txt

echo "[post-create] 完成。Flask: http://127.0.0.1:5000  pgAdmin: http://127.0.0.1:5050"
