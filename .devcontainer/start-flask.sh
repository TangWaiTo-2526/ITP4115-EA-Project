#!/usr/bin/env bash
# 在背景啟動 Flask，讓 postStartCommand 能立刻結束（不阻塞 Dev Containers）
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export FLASK_APP=app
LOG=/tmp/flask-dev.log
PIDFILE=/tmp/flask-dev.pid

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "[post-start] Flask 已在執行 (PID $(cat "$PIDFILE"))，略過。"
  exit 0
fi

nohup flask run --debug --host=0.0.0.0 --port 5000 >>"$LOG" 2>&1 &
echo $! >"$PIDFILE"
echo "[post-start] Flask 已在背景啟動 (PID $(cat "$PIDFILE"))，日誌: $LOG"
echo "[post-start] 瀏覽: http://127.0.0.1:5000 （Codespaces 會轉發埠 5000）"
