from sre_agent.models.domain import Plan

CATALOG = {"rollback_deployment", "scale_deployment", "restart_deployment", "delete_failed_pod"}
def evaluate(plan: Plan, environment: str, approved: bool = False) -> tuple[bool, str]:
    if plan.action not in CATALOG: return False, "unknown remediation capability"
    if plan.action == "scale_deployment" and (plan.desired_replicas is None or plan.desired_replicas > 10): return False, "scale exceeds configured maximum"
    if plan.namespace in {"kube-system", "production"} and environment != "production": return False, "cross-environment target denied"
    if environment == "production" and not approved: return False, "production write requires approval"
    return True, "allowed"
