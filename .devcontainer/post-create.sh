#!/usr/bin/env bash
# Codespace / devcontainer 建立後自動執行：啟動 Docker 資料庫、安裝 Python 依賴
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TOTAL_STEPS=3

log() {
  printf '[post-create %s] %s\n' "$(date '+%H:%M:%S')" "$*"
}

step_header() {
  local n=$1
  local title=$2
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  printf '  [%s/%s] %s\n' "$n" "$TOTAL_STEPS" "$title"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

wait_for_docker() {
  local max_attempts=${1:-90}
  local i=0
  log "等待 Docker daemon（最多約 $((max_attempts * 2)) 秒，每 2 秒重試一次）..."
  while ! docker info >/dev/null 2>&1; do
    i=$((i + 1))
    if [ "$i" -ge "$max_attempts" ]; then
      log "警告: Docker 在逾時內仍未就緒，略過 compose；可稍後手動: docker compose up -d" >&2
      return 1
    fi
    printf '[post-create %s]   ... Docker 尚未就緒 (%s/%s)\r' "$(date '+%H:%M:%S')" "$i" "$max_attempts"
  done
  echo ""
  log "Docker daemon 已就緒。"
  return 0
}

log "workspace: $ROOT"

# --- 1. Docker ---
step_header 1 "Docker：PostgreSQL + pgAdmin"
if ! command -v docker >/dev/null 2>&1; then
  log "警告: 未找到 docker 命令，略過 compose。" >&2
else
  if wait_for_docker; then
    log "拉取映像（首次或版本更新時可能較久，下方會顯示各層進度）..."
    docker compose pull 2>&1 || log "提示: pull 未完成（可能離線或已有映像），仍嘗試啟動..."
    log "啟動容器..."
    docker compose up -d 2>&1 || log "警告: docker compose up 失敗，可稍後手動: docker compose up -d" >&2
  fi
fi

# --- 2. pip ---
step_header 2 "Python：升級 pip / setuptools / wheel"
export PIP_PROGRESS_BAR=on
log "執行: python3 -m pip install -U pip setuptools wheel"
python3 -m pip install -U pip setuptools wheel

step_header 3 "Python：安裝 requirements.txt"
log "執行: python3 -m pip install -r requirements.txt（依套件數量可能需數分鐘）"
python3 -m pip install -r requirements.txt
