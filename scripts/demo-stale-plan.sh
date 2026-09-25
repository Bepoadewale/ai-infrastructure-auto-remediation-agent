#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
"$(dirname "$0")/smoke.sh"
kubectl -n "$NAMESPACE" set env deployment/checkout-api BROKEN=1
sleep 4
payload='{"service":"checkout-api","namespace":"sre-remediation","environment":"production","alert_name":"CheckoutUnavailable","fingerprint":"checkout-stale-plan-demo"}'
incident="$(curl -fsS -X POST -H 'Authorization: Bearer agent-demo' -H 'content-type: application/json' http://127.0.0.1:18070/api/v1/incidents -d "$payload" | "$ROOT/.venv/bin/python" -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
for action in investigate diagnose plan; do
  curl -fsS -X POST -H 'Authorization: Bearer agent-demo' "http://127.0.0.1:18070/api/v1/incidents/$incident/$action" >/dev/null
done
kubectl -n "$NAMESPACE" annotate deployment/checkout-api sre.platform/stale-demo="$(date +%s)" --overwrite
curl -fsS -X POST -H 'Authorization: Bearer approver-demo' "http://127.0.0.1:18070/api/v1/incidents/$incident/approve" >/dev/null
status="$(curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Authorization: Bearer operator-demo' "http://127.0.0.1:18070/api/v1/incidents/$incident/remediate")"
[[ "$status" == 409 ]] || { echo "expected stale-plan rejection, got $status" >&2; exit 1; }
kubectl -n "$NAMESPACE" set env deployment/checkout-api BROKEN=0
kubectl -n "$NAMESPACE" rollout status deployment/checkout-api --timeout=90s
echo "demo-stale-plan: changed Kubernetes resource rejected the outdated approved plan"
