from __future__ import annotations

import hashlib
import os
import time
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException
from prometheus_client import make_asgi_app
from sre_agent.diagnosis.rules import diagnose
from sre_agent.models.domain import Evidence, Incident, IncidentCreate, IncidentStatus, Plan, Risk
from sre_agent.policy.engine import evaluate
from sre_agent.remediation.executor import KubernetesExecutor, LocalLabExecutor
from sre_agent.store import IncidentStore
from sre_agent.telemetry import ACTIONS, INCIDENTS, PLANS, VERIFY_SECONDS

app = FastAPI(title="Governed AI SRE Auto-Remediation", version="0.2.0")
app.mount("/metrics", make_asgi_app())
store = IncidentStore(os.getenv("SRE_DATABASE", ".local/remediation.db"))
executor = LocalLabExecutor() if os.getenv("SRE_EXECUTOR", "local") == "local" else KubernetesExecutor()


def role(authorization: str = Header(...)) -> str:
    roles = {
        "Bearer agent-demo": "agent-investigator",
        "Bearer operator-demo": "remediation-operator",
        "Bearer approver-demo": "incident-approver",
    }
    if authorization not in roles:
        raise HTTPException(401, "invalid credentials")
    return roles[authorization]


def get_incident(incident_id: str) -> Incident:
    incident = store.get(incident_id)
    if not incident:
        raise HTTPException(404, "not found")
    return incident


def persist(incident: Incident, name: str, principal: str = "system", detail: str | None = None) -> Incident:
    incident.timeline.append({"timestamp": datetime.now(UTC).isoformat(), "event": name, "principal": principal, "detail": detail})
    store.save(incident)
    return incident


def plan_digest(incident: Incident, plan: Plan) -> str:
    stable = f"{incident.id}:{plan.action}:{plan.target}:{plan.namespace}:{plan.expected_resource_version}:{plan.expected_broken}:{plan.expected_image}:{plan.plan_version}"
    return hashlib.sha256(stable.encode()).hexdigest()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "executor": type(executor).__name__}


@app.post("/api/v1/incidents")
def create(payload: IncidentCreate, principal: str = Depends(role)) -> Incident:
    existing = store.active_by_fingerprint(payload.fingerprint)
    if existing:
        return existing
    incident = Incident(id=f"INC-{uuid4().hex[:8]}", **payload.model_dump())
    INCIDENTS.labels(status="detected").inc()
    return persist(incident, "INCIDENT_DETECTED", principal)


@app.get("/api/v1/incidents")
def list_incidents(principal: str = Depends(role)) -> list[Incident]:
    return store.list()


@app.get("/api/v1/incidents/{incident_id}")
def get(incident_id: str, principal: str = Depends(role)) -> Incident:
    return get_incident(incident_id)


@app.get("/api/v1/incidents/{incident_id}/timeline")
def timeline(incident_id: str, principal: str = Depends(role)) -> list[dict]:
    return get_incident(incident_id).timeline


@app.post("/api/v1/incidents/{incident_id}/investigate")
def investigate(incident_id: str, principal: str = Depends(role)) -> list[Evidence]:
    incident = get_incident(incident_id)
    if principal not in {"agent-investigator", "remediation-operator"}:
        raise HTTPException(403, "investigator role required")
    incident.status = IncidentStatus.INVESTIGATING
    try:
        raw = executor.evidence(incident.service, incident.namespace)
    except Exception as error:
        incident.status = IncidentStatus.ESCALATED
        persist(incident, "EVIDENCE_COLLECTION_FAILED", principal, str(error))
        raise HTTPException(502, "cluster evidence unavailable") from error
    incident.evidence = [
        Evidence(id=f"ev-{index}", type=item["type"], source=item["source"], observation=item["observation"], timestamp=datetime.now(UTC), supports=["deployment_regression"])
        for index, item in enumerate(raw)
    ]
    persist(incident, "EVIDENCE_COLLECTED", principal)
    return incident.evidence


@app.post("/api/v1/incidents/{incident_id}/diagnose")
def diagnosis(incident_id: str, principal: str = Depends(role)) -> dict:
    incident = get_incident(incident_id)
    if not incident.evidence:
        raise HTTPException(409, "investigation evidence required")
    incident.diagnosis = diagnose(incident.evidence)
    incident.status = IncidentStatus.DIAGNOSING
    persist(incident, "DIAGNOSIS_CREATED", principal)
    return incident.diagnosis


@app.post("/api/v1/incidents/{incident_id}/plan")
def plan(incident_id: str, principal: str = Depends(role)) -> Plan:
    incident = get_incident(incident_id)
    action = (incident.diagnosis or {}).get("proposed_action")
    if not action:
        raise HTTPException(409, "insufficient evidence for plan")
    draft = Plan(action=action, target=incident.service, namespace=incident.namespace, risk=Risk.HIGH, reversible=True)
    try:
        snapshot = executor.snapshot(draft)
    except Exception as error:
        raise HTTPException(502, "unable to read current target state") from error
    incident.plan = draft.model_copy(update={
        "current_replicas": snapshot["replicas"],
        "expected_resource_version": snapshot["resource_version"],
        "expected_broken": snapshot["broken"],
        "expected_image": snapshot["image"],
    })
    incident.plan.plan_hash = plan_digest(incident, incident.plan)
    incident.status = IncidentStatus.PLAN_PROPOSED
    allowed, reason = evaluate(incident.plan, incident.environment, False)
    PLANS.labels(result="approval_required" if not allowed else "allowed").inc()
    persist(incident, "PLAN_PROPOSED", principal, f"policy={reason}; hash={incident.plan.plan_hash}")
    return incident.plan


@app.post("/api/v1/incidents/{incident_id}/approve")
def approve(incident_id: str, principal: str = Depends(role)) -> Plan:
    if principal != "incident-approver":
        raise HTTPException(403, "separate approver role required")
    incident = get_incident(incident_id)
    if not incident.plan:
        raise HTTPException(409, "plan required")
    if any(item["principal"] == principal and item["event"] == "PLAN_PROPOSED" for item in incident.timeline):
        raise HTTPException(403, "plan requester cannot self-approve")
    incident.plan.approved_by = principal
    incident.status = IncidentStatus.APPROVED
    persist(incident, "PLAN_APPROVED", principal, incident.plan.plan_hash)
    return incident.plan


@app.post("/api/v1/incidents/{incident_id}/remediate")
def remediate(incident_id: str, principal: str = Depends(role)) -> Incident:
    if principal != "remediation-operator":
        raise HTTPException(403, "operator role required")
    incident = get_incident(incident_id)
    if not incident.plan:
        raise HTTPException(409, "plan required")
    allowed, reason = evaluate(incident.plan, incident.environment, bool(incident.plan.approved_by))
    if not allowed:
        incident.status = IncidentStatus.APPROVAL_REQUIRED
        PLANS.labels(result="denied").inc()
        persist(incident, "POLICY_DENIED", principal, reason)
        raise HTTPException(403, reason)
    if not executor.precondition(incident.plan):
        persist(incident, "STALE_PLAN_DENIED", principal)
        raise HTTPException(409, "stale plan precondition failed")
    reserved, reservation_reason = store.reserve_remediation(
        incident.service, cooldown_seconds=int(os.getenv("SRE_COOLDOWN_SECONDS", "30"))
    )
    if not reserved:
        persist(incident, "REMEDIATION_GUARD_DENIED", principal, reservation_reason)
        raise HTTPException(409, reservation_reason)
    incident.status = IncidentStatus.REMEDIATING
    persist(incident, "REMEDIATION_STARTED", principal)
    try:
        result = executor.apply(incident.plan)
    except Exception as error:
        incident.status = IncidentStatus.ESCALATED
        ACTIONS.labels(action=incident.plan.action, result="failed").inc()
        persist(incident, "REMEDIATION_FAILED", principal, str(error))
        raise HTTPException(502, "bounded remediation failed") from error
    ACTIONS.labels(action=incident.plan.action, result="applied").inc()
    incident.status = IncidentStatus.VERIFYING
    start = time.monotonic()
    verified = executor.verify(incident.plan)
    VERIFY_SECONDS.observe(time.monotonic() - start)
    if not verified:
        incident.status = IncidentStatus.ESCALATED
        ACTIONS.labels(action=incident.plan.action, result="verification_failed").inc()
        return persist(incident, "VERIFICATION_FAILED", principal, result)
    incident.status = IncidentStatus.RESOLVED
    INCIDENTS.labels(status="resolved").inc()
    return persist(incident, "INCIDENT_RESOLVED", principal, result)
