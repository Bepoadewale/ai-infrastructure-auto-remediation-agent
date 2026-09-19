from fastapi.testclient import TestClient
from sre_agent.main import app, executor

client=TestClient(app)
AGENT={"Authorization":"Bearer agent-demo"}; OP={"Authorization":"Bearer operator-demo"}; APPROVER={"Authorization":"Bearer approver-demo"}
def create(environment="production", fingerprint="bad-v2"):
    return client.post("/api/v1/incidents",headers=AGENT,json={"service":"checkout-api","namespace":"shop","environment":environment,"alert_name":"High5xx","fingerprint":fingerprint}).json()["id"]
def test_bad_deployment_requires_approval_then_recovers():
    executor.state["checkout-api"]={"revision":"v2","replicas":3,"healthy":False}; incident=create()
    assert client.post(f"/api/v1/incidents/{incident}/investigate",headers=AGENT).status_code==200
    assert client.post(f"/api/v1/incidents/{incident}/diagnose",headers=AGENT).json()["root_cause"]=="deployment_regression"
    assert client.post(f"/api/v1/incidents/{incident}/plan",headers=AGENT).status_code==200
    assert client.post(f"/api/v1/incidents/{incident}/remediate",headers=OP).status_code==403
    client.post(f"/api/v1/incidents/{incident}/approve",headers=APPROVER)
    assert client.post(f"/api/v1/incidents/{incident}/remediate",headers=OP).json()["status"]=="RESOLVED"
    assert executor.state["checkout-api"]["revision"]=="v1"
def test_unsafe_action_is_not_a_capability():
    from sre_agent.models.domain import Plan, Risk
    from sre_agent.policy.engine import evaluate
    assert evaluate(Plan(action="delete_namespace",target="production",namespace="production",risk=Risk.CRITICAL,reversible=False),"production",True)[0] is False
def test_duplicate_alert_deduplicates_active_incident():
    assert create("dev","duplicate") == create("dev","duplicate")
def test_stale_plan_does_not_mutate():
    executor.state["checkout-api"]={"revision":"v2","replicas":6,"healthy":False}; incident=create("dev","stale")
    client.post(f"/api/v1/incidents/{incident}/investigate",headers=AGENT); client.post(f"/api/v1/incidents/{incident}/diagnose",headers=AGENT); client.post(f"/api/v1/incidents/{incident}/plan",headers=AGENT)
    assert client.post(f"/api/v1/incidents/{incident}/remediate",headers=OP).status_code==409
