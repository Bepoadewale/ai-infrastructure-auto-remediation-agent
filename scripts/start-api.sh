#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
[[ -x "$ROOT/.venv/bin/python" ]] || { echo "Run make install first" >&2; exit 1; }
if [[ -f "$LOCAL_DIR/api.pid" ]] && kill -0 "$(cat "$LOCAL_DIR/api.pid")" 2>/dev/null; then exit 0; fi
SRE_EXECUTOR=kubernetes SRE_COOLDOWN_SECONDS=0 KUBE_CONTEXT="kind-$CLUSTER_NAME" SRE_DATABASE="$LOCAL_DIR/remediation.db" "$ROOT/.venv/bin/python" -m uvicorn sre_agent.main:app --host 127.0.0.1 --port 18070 >"$LOCAL_DIR/api.log" 2>&1 &
echo $! >"$LOCAL_DIR/api.pid"
wait_for "control plane" "curl -fsS http://127.0.0.1:18070/healthz" 45
