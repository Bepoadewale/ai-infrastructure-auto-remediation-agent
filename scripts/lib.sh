#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLUSTER_NAME="ai-sre-remediation"
NAMESPACE="sre-remediation"
LOCAL_DIR="$ROOT/.local"
mkdir -p "$LOCAL_DIR"
wait_for() {
  local description="$1" command="$2" timeout="${3:-90}" elapsed=0
  until eval "$command" >/dev/null 2>&1; do
    if (( elapsed >= timeout )); then echo "Timed out waiting for $description" >&2; return 1; fi
    sleep 2; elapsed=$((elapsed + 2))
  done
}
start_port_forward() {
  local name="$1" resource="$2" port="$3" host_port="${3%%:*}"
  local log="$LOCAL_DIR/${name}-port-forward.log"
  local pid="$LOCAL_DIR/${name}-port-forward.pid"
  if [[ -f "$pid" ]] && kill -0 "$(cat "$pid")" 2>/dev/null; then return; fi
  nohup kubectl -n "$NAMESPACE" port-forward "$resource" "$port" >"$log" 2>&1 < /dev/null & echo $! >"$pid"
  wait_for "$name port forward" "curl -fsS http://localhost:$host_port/ >/dev/null" 45
}
stop_port_forwards() {
  for pid in "$LOCAL_DIR"/*-port-forward.pid "$LOCAL_DIR"/api.pid; do
    [[ -f "$pid" ]] || continue
    kill "$(cat "$pid")" 2>/dev/null || true
    rm -f "$pid"
  done
}
