from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class IncidentStatus(StrEnum):
    DETECTED="DETECTED"; INVESTIGATING="INVESTIGATING"; DIAGNOSING="DIAGNOSING"; PLAN_PROPOSED="PLAN_PROPOSED"; APPROVAL_REQUIRED="APPROVAL_REQUIRED"; APPROVED="APPROVED"; REMEDIATING="REMEDIATING"; VERIFYING="VERIFYING"; RESOLVED="RESOLVED"; FAILED="FAILED"; ESCALATED="ESCALATED"
class Risk(StrEnum):
    READ_ONLY="RISK_0"; LOW="RISK_1"; MODERATE="RISK_2"; HIGH="RISK_3"; CRITICAL="RISK_4"
class Evidence(BaseModel):
    id: str; type: str; source: str; observation: str; timestamp: datetime; supports: list[str] = []
class IncidentCreate(BaseModel):
    service: str; namespace: str; environment: str; alert_name: str; severity: str = "SEV2"; fingerprint: str
class Plan(BaseModel):
    action: str; target: str; namespace: str; current_replicas: int | None = None; desired_replicas: int | None = None; risk: Risk; reversible: bool; plan_version: int = 1; approved_by: str | None = None
class Incident(BaseModel):
    id: str; service: str; namespace: str; environment: str; alert_name: str; severity: str; fingerprint: str; status: IncidentStatus = IncidentStatus.DETECTED; created_at: datetime = Field(default_factory=lambda: datetime.now(UTC)); evidence: list[Evidence] = []; diagnosis: dict | None = None; plan: Plan | None = None; timeline: list[dict] = []
