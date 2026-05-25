#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-python3}"

PY_VERSION="$($PYTHON_BIN - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)"

if "$PYTHON_BIN" - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 9) else 1)
PY
then
  :
else
  echo "当前 Python 版本是 ${PY_VERSION}，本项目需要 Python 3.9+。"
  echo "请先安装 Python 3.9+，然后重新运行：./start_web.sh"
  exit 1
fi

if "$PYTHON_BIN" - <<'PY'
import streamlit
PY
then
  :
else
  "$PYTHON_BIN" -m pip install --upgrade pip
  "$PYTHON_BIN" -m pip install --no-cache-dir --timeout 120 -r requirements.txt
fi

echo ""
echo "Steam Game Insight Copilot 网页已启动："
echo "http://localhost:8501"
echo ""

STREAMLIT_BROWSER_GATHER_USAGE_STATS=false "$PYTHON_BIN" -m streamlit run app.py --server.port 8501 --server.headless true
