from sre_agent.models.domain import Plan


class LocalLabExecutor:
    """Deterministic lab executor; replace with narrow Kubernetes API client in cluster mode."""
    def __init__(self): self.state = {"checkout-api": {"revision":"v2", "replicas":3, "healthy":False}}
    def precondition(self, plan: Plan) -> bool:
        item=self.state.get(plan.target); return bool(item and (plan.current_replicas is None or item["replicas"] == plan.current_replicas))
    def apply(self, plan: Plan) -> str:
        item=self.state[plan.target]
        if plan.action == "rollback_deployment": item.update(revision="v1", healthy=True); return "rolled back v2 to v1"
        if plan.action == "scale_deployment":
            if item["replicas"] == plan.desired_replicas: return "NO_CHANGE"
            item["replicas"] = plan.desired_replicas; item["healthy"] = True; return f"scaled to {plan.desired_replicas}"
        raise ValueError("unsupported executor action")
    def verify(self, plan: Plan) -> bool: return self.state[plan.target]["healthy"]
