from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException
from sre_agent.diagnosis.rules import diagnose
from sre_agent.models.domain import Evidence, Incident, IncidentCreate, IncidentStatus, Plan, Risk
from sre_agent.policy.engine import evaluate
from sre_agent.remediation.executor import LocalLabExecutor

app=FastAPI(title="Governed AI SRE Auto-Remediation", version="0.1.0")
incidents: dict[str, Incident] = {}; executor=LocalLabExecutor()
def role(authorization: str=Header(...)):
    roles={"Bearer agent-demo":"agent-investigator", "Bearer operator-demo":"remediation-operator", "Bearer approver-demo":"incident-approver"}
    if authorization not in roles: raise HTTPException(401,"invalid credentials")
    return roles[authorization]
def event(incident: Incident, name: str, principal="system"):
    incident.timeline.append({"timestamp":datetime.now(UTC).isoformat(),"event":name,"principal":principal})

@app.post("/api/v1/incidents")
def create(payload: IncidentCreate, principal=Depends(role)):
    existing=next((i for i in incidents.values() if i.fingerprint==payload.fingerprint and i.status not in {IncidentStatus.RESOLVED,IncidentStatus.FAILED}),None)
    if existing: return existing
    incident=Incident(id=f"INC-{uuid4().hex[:8]}",**payload.model_dump()); event(incident,"INCIDENT_DETECTED",principal); incidents[incident.id]=incident; return incident
@app.get("/api/v1/incidents")
def list_incidents(principal=Depends(role)): return list(incidents.values())
@app.get("/api/v1/incidents/{incident_id}")
def get_incident(incident_id:str, principal=Depends(role)): return incidents.get(incident_id) or (_ for _ in ()).throw(HTTPException(404,"not found"))
@app.get("/api/v1/incidents/{incident_id}/timeline")
def timeline(incident_id:str, principal=Depends(role)): return get_incident(incident_id,principal).timeline
@app.post("/api/v1/incidents/{incident_id}/investigate")
def investigate(incident_id:str, principal=Depends(role)):
    incident=get_incident(incident_id,principal); incident.status=IncidentStatus.INVESTIGATING
    incident.evidence=[Evidence(id="ev-5xx",type="metric",source="prometheus",observation="HTTP 5xx increased from 0.2% to 14%",timestamp=datetime.now(UTC),supports=["deployment_regression"]),Evidence(id="ev-ready",type="kubernetes_event",source="deployment/checkout-api",observation="v2 pods have readiness probe failures",timestamp=datetime.now(UTC),supports=["deployment_regression"]),Evidence(id="ev-deploy",type="deployment",source="checkout-api",observation="v2 deployed 7 minutes before error spike",timestamp=datetime.now(UTC),supports=["deployment_regression"])]
    event(incident,"EVIDENCE_COLLECTED",principal); return incident.evidence
@app.post("/api/v1/incidents/{incident_id}/diagnose")
def diagnosis(incident_id:str, principal=Depends(role)):
    incident=get_incident(incident_id,principal); incident.diagnosis=diagnose(incident.evidence); incident.status=IncidentStatus.DIAGNOSING; event(incident,"DIAGNOSIS_CREATED",principal); return incident.diagnosis
@app.post("/api/v1/incidents/{incident_id}/plan")
def plan(incident_id:str, principal=Depends(role)):
    incident=get_incident(incident_id,principal); action=(incident.diagnosis or {}).get("proposed_action")
    if not action: raise HTTPException(409,"insufficient evidence for plan")
    incident.plan=Plan(action=action,target=incident.service,namespace=incident.namespace,current_replicas=3,risk=Risk.HIGH,reversible=True); incident.status=IncidentStatus.PLAN_PROPOSED; event(incident,"PLAN_PROPOSED",principal); return incident.plan
@app.post("/api/v1/incidents/{incident_id}/approve")
def approve(incident_id:str, principal=Depends(role)):
    if principal!="incident-approver": raise HTTPException(403,"approver role required")
    incident=get_incident(incident_id,principal); incident.plan.approved_by=principal; incident.status=IncidentStatus.APPROVED; event(incident,"PLAN_APPROVED",principal); return incident.plan
@app.post("/api/v1/incidents/{incident_id}/remediate")
def remediate(incident_id:str, principal=Depends(role)):
    if principal!="remediation-operator": raise HTTPException(403,"operator role required")
    incident=get_incident(incident_id,principal); allowed,reason=evaluate(incident.plan,incident.environment,bool(incident.plan.approved_by))
    if not allowed: incident.status=IncidentStatus.APPROVAL_REQUIRED; event(incident,f"POLICY_DENIED:{reason}",principal); raise HTTPException(403,reason)
    if not executor.precondition(incident.plan): raise HTTPException(409,"stale plan precondition failed")
    incident.status=IncidentStatus.REMEDIATING; result=executor.apply(incident.plan); event(incident,f"ACTION_EXECUTED:{result}",principal); incident.status=IncidentStatus.VERIFYING
    if not executor.verify(incident.plan): incident.status=IncidentStatus.ESCALATED; event(incident,"VERIFICATION_FAILED",principal); return incident
    incident.status=IncidentStatus.RESOLVED; event(incident,"INCIDENT_RESOLVED",principal); return incident
