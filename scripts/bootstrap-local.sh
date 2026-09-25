#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
command -v docker >/dev/null || { echo "Docker Desktop is required" >&2; exit 1; }
docker info >/dev/null || { echo "Docker Desktop is not running" >&2; exit 1; }
command -v kind >/dev/null; command -v kubectl >/dev/null
if ! kind get clusters | grep -qx "$CLUSTER_NAME"; then kind create cluster --name "$CLUSTER_NAME" --config "$ROOT/local/kind-config.yaml"; fi
docker build -t autoremediation-checkout:local -f "$ROOT/local/Dockerfile.checkout" "$ROOT"
kind load docker-image autoremediation-checkout:local --name "$CLUSTER_NAME"
kubectl apply -k "$ROOT/local/k8s"
kubectl -n "$NAMESPACE" rollout status deployment/prometheus --timeout=120s
kubectl -n "$NAMESPACE" rollout status deployment/checkout-api --timeout=120s
start_port_forward prometheus service/prometheus 19090:9090
echo "Bootstrap complete: kind=$CLUSTER_NAME, Prometheus=http://localhost:19090"
