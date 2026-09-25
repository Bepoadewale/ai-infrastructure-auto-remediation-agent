#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
"$(dirname "$0")/smoke.sh"
kubectl -n "$NAMESPACE" set image deployment/checkout-api checkout=invalid.local/checkout:missing
sleep 5
payload='{"service":"checkout-api","namespace":"sre-remediation","environment":"production","alert_name":"CheckoutImagePullFailure","fingerprint":"checkout-image-pull-demo"}'
incident="$(curl -fsS -X POST -H 'Authorization: Bearer agent-demo' -H 'content-type: application/json' http://127.0.0.1:18070/api/v1/incidents -d "$payload" | "$ROOT/.venv/bin/python" -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
for action in investigate diagnose plan; do
  curl -fsS -X POST -H 'Authorization: Bearer agent-demo' "http://127.0.0.1:18070/api/v1/incidents/$incident/$action" >/dev/null
done
curl -fsS -X POST -H 'Authorization: Bearer approver-demo' "http://127.0.0.1:18070/api/v1/incidents/$incident/approve" >/dev/null
result="$(curl -fsS -X POST -H 'Authorization: Bearer operator-demo' "http://127.0.0.1:18070/api/v1/incidents/$incident/remediate")"
echo "$result" | "$ROOT/.venv/bin/python" -c 'import json,sys; r=json.load(sys.stdin); assert r["status"] == "RESOLVED", r; print("demo-image-recovery: image pull failure recovered by allowlisted rollback")'
kubectl -n "$NAMESPACE" rollout status deployment/checkout-api --timeout=90s
