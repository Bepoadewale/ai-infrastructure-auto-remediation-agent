from sre_agent.models.domain import Evidence


def diagnose(evidence: list[Evidence]) -> dict:
    text = " ".join(f"{item.source} {item.observation}".lower() for item in evidence)
    if ("readiness" in text or "available_replicas=0" in text) and ("5xx" in text or "checkout" in text or "deployment" in text):
        return {"root_cause":"deployment_regression", "confidence":0.91, "supporting_evidence":[e.id for e in evidence], "contradicting_evidence":[], "proposed_action":"rollback_deployment"}
    if "cpu" in text and "latency" in text and "traffic" in text:
        return {"root_cause":"capacity_saturation", "confidence":0.82, "supporting_evidence":[e.id for e in evidence], "contradicting_evidence":[], "proposed_action":"scale_deployment"}
    return {"root_cause":"insufficient_evidence", "confidence":0.2, "supporting_evidence":[e.id for e in evidence], "contradicting_evidence":[], "proposed_action":None}
