#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ensure_python313() {
  if command -v python3.13 >/dev/null 2>&1; then
    return
  fi
  if ! command -v apt-get >/dev/null 2>&1; then
    echo "python3.13 is required (interpreter_constraints ==3.13.*)" >&2
    exit 1
  fi
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends software-properties-common
  sudo add-apt-repository -y ppa:deadsnakes/ppa
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends python3.13 python3.13-venv python3.13-dev
}

ensure_python313

PYTHON_BIN="${PYTHON_BIN:-$(command -v python3.13)}"
"$PYTHON_BIN" -c 'import sys; assert sys.version_info[:2] == (3, 13), sys.version'

if [[ ! -d "$ROOT/venv" ]]; then
  "$PYTHON_BIN" -m venv "$ROOT/venv"
fi

# shellcheck disable=SC1091
source "$ROOT/venv/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r "$ROOT/requirements.txt" -r "$ROOT/full_requirements.txt" \
  -r "$ROOT/extra_requirements.txt" -r "$ROOT/dev_requirements.txt"
python -m pip install -r "$ROOT/packages/trading/requirements.txt" \
  -r "$ROOT/packages/commons/requirements.txt" \
  -r "$ROOT/packages/commons/full_requirements.txt" \
  -r "$ROOT/packages/sync/requirements.txt" \
  -r "$ROOT/packages/services/full_requirements.txt" \
  -r "$ROOT/packages/tentacles_manager/requirements.txt" \
  -r "$ROOT/packages/tentacles_manager/full_requirements.txt"

export ROOT
export PYTHONPATH="$ROOT:$ROOT/packages:$ROOT/packages/agents:$ROOT/packages/async_channel:$ROOT/packages/backtesting:$ROOT/packages/binary:$ROOT/packages/commons:$ROOT/packages/copy:$ROOT/packages/evaluators:$ROOT/packages/flow:$ROOT/packages/node:$ROOT/packages/protocol:$ROOT/packages/services:$ROOT/packages/sync:$ROOT/packages/tentacles:$ROOT/packages/tentacles_manager:$ROOT/packages/trading"

python "$ROOT/packages/tentacles/Services/Services_bases/marketing_assets_service/cli.py" \
  --output "$ROOT/user/marketing_assets"

echo "OctoBot environment install complete"
echo "Python: $(python --version)"
echo "Marketing cards: $ROOT/user/marketing_assets"
