#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
kubectl config current-context | grep -qx "kind-$CLUSTER_NAME"
kubectl -n "$NAMESPACE" get deployment checkout-api prometheus >/dev/null
start_port_forward prometheus service/prometheus 19090:9090
curl -fsS http://localhost:19090/-/ready >/dev/null
"$(dirname "$0")/start-api.sh"
curl -fsS http://127.0.0.1:18070/healthz >/dev/null
echo "smoke: kind, Prometheus, checkout fixture, and control plane are ready"
