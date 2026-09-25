#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
"$(dirname "$0")/smoke.sh"
kubectl -n "$NAMESPACE" set env deployment/checkout-api BROKEN=1
kubectl -n "$NAMESPACE" rollout status deployment/checkout-api --timeout=10s >/dev/null 2>&1 && { echo "fixture unexpectedly became ready" >&2; exit 1; } || true
payload='{"service":"checkout-api","namespace":"sre-remediation","environment":"production","alert_name":"CheckoutUnavailable","fingerprint":"unsafe-demo"}'
incident="$(curl -fsS -X POST -H 'Authorization: Bearer agent-demo' -H 'content-type: application/json' http://127.0.0.1:18070/api/v1/incidents -d "$payload" | "$ROOT/.venv/bin/python" -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
for action in investigate diagnose plan; do
  curl -fsS -X POST -H 'Authorization: Bearer agent-demo' "http://127.0.0.1:18070/api/v1/incidents/$incident/$action" >/dev/null
done
status="$(curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Authorization: Bearer operator-demo' "http://127.0.0.1:18070/api/v1/incidents/$incident/remediate")"
[[ "$status" == 403 ]] || { echo "expected unapproved production remediation denial, got $status" >&2; exit 1; }
echo "demo-rollback: production action was denied until a separate approval exists"
