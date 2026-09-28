#!/usr/bin/env bash
set -eo pipefail
TASK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/humble/setup.bash
source "$TASK_ROOT/install/setup.bash"
export ROS_DOMAIN_ID=42
export PYTHONPATH="$TASK_ROOT/src/ur3_llm_control:${PYTHONPATH:-}"
if [[ -f "$TASK_ROOT/.runtime/nine-api-key" ]]; then
  export NINEROUTER_API_KEY="$(cat "$TASK_ROOT/.runtime/nine-api-key")"
  export NINEROUTER_MODEL="${NINEROUTER_MODEL:-oc/mimo-v2.5-free}"
  export NINEROUTER_WINDOWS_BRIDGE="$(wslpath -w "$TASK_ROOT/scripts/http_bridge.cjs")"
fi
cd "$TASK_ROOT"
exec ros2 run ur3_llm_control skill_executor "$@"
