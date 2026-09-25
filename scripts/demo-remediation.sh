#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
"$(dirname "$0")/smoke.sh"
kubectl -n "$NAMESPACE" set env deployment/checkout-api BROKEN=1
kubectl -n "$NAMESPACE" rollout status deployment/checkout-api --timeout=10s >/dev/null 2>&1 && { echo "fixture unexpectedly became ready" >&2; exit 1; } || true
wait_for "Prometheus alert" "curl -fsS 'http://localhost:19090/api/v1/query?query=ALERTS%7Balertname%3D%22CheckoutUnavailable%22%2Calertstate%3D%22firing%22%7D' | grep -q CheckoutUnavailable" 90
create='{"service":"checkout-api","namespace":"sre-remediation","environment":"production","alert_name":"CheckoutUnavailable","fingerprint":"checkout-unavailable-demo"}'
incident="$(curl -fsS -X POST -H 'Authorization: Bearer agent-demo' -H 'content-type: application/json' http://127.0.0.1:18070/api/v1/incidents -d "$create" | "$ROOT/.venv/bin/python" -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
for action in investigate diagnose plan; do
  curl -fsS -X POST -H 'Authorization: Bearer agent-demo' "http://127.0.0.1:18070/api/v1/incidents/$incident/$action" >/dev/null
done
curl -fsS -X POST -H 'Authorization: Bearer approver-demo' "http://127.0.0.1:18070/api/v1/incidents/$incident/approve" >/dev/null
result="$(curl -fsS -X POST -H 'Authorization: Bearer operator-demo' "http://127.0.0.1:18070/api/v1/incidents/$incident/remediate")"
echo "$result" | "$ROOT/.venv/bin/python" -c 'import json,sys; r=json.load(sys.stdin); assert r["status"] == "RESOLVED", r; print("demo-remediation: incident", r["id"], "resolved after guarded Kubernetes rollback")'
kubectl -n "$NAMESPACE" rollout status deployment/checkout-api --timeout=90s
