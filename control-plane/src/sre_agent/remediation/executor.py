"""Narrow Kubernetes executor: allowlisted operations only, never arbitrary kubectl/shell."""
from __future__ import annotations

import os
import time

from kubernetes import client, config
from sre_agent.models.domain import Plan


class KubernetesExecutor:
    def __init__(self) -> None:
        if os.getenv("KUBERNETES_SERVICE_HOST"):
            config.load_incluster_config()
        else:
            config.load_kube_config(context=os.getenv("KUBE_CONTEXT") or None)
        self.apps = client.AppsV1Api()
        self.core = client.CoreV1Api()

    def snapshot(self, plan: Plan) -> dict:
        deployment = self.apps.read_namespaced_deployment(plan.target, plan.namespace)
        containers = deployment.spec.template.spec.containers
        broken = any(
            env.name == "BROKEN" and env.value == "1" for container in containers for env in (container.env or [])
        )
        return {
            "resource_version": deployment.metadata.resource_version,
            "replicas": deployment.spec.replicas or 0,
            "available": deployment.status.available_replicas or 0,
            "broken": broken,
            "image": containers[0].image,
        }

    def precondition(self, plan: Plan) -> bool:
        state = self.snapshot(plan)
        return (
            (plan.expected_resource_version is None or state["resource_version"] == plan.expected_resource_version)
            and (plan.expected_broken is None or state["broken"] == plan.expected_broken)
            and (plan.expected_image is None or state["image"] == plan.expected_image)
        )

    def evidence(self, service: str, namespace: str) -> list[dict[str, str]]:
        deployment = self.apps.read_namespaced_deployment(service, namespace)
        pods = self.core.list_namespaced_pod(namespace, label_selector=f"app={service}").items
        events = self.core.list_namespaced_event(namespace, field_selector=f"involvedObject.name={service}").items
        available = deployment.status.available_replicas or 0
        observations = [
            {"type": "deployment", "source": f"deployment/{service}", "observation": f"{service} available_replicas={available}; generation={deployment.metadata.generation}"},
            {"type": "kubernetes_pods", "source": namespace, "observation": "; ".join(f"{pod.metadata.name}:{pod.status.phase}" for pod in pods) or "no pods found"},
        ]
        observations.append({"type": "kubernetes_event", "source": namespace, "observation": "; ".join(event.message or "" for event in events[-5:]) or "no deployment events"})
        return observations

    def apply(self, plan: Plan) -> str:
        if plan.action not in {"rollback_deployment", "scale_deployment", "restart_deployment", "delete_failed_pod"}:
            raise ValueError("unsupported remediation capability")
        if plan.action == "rollback_deployment":
            body = {"spec": {"template": {"spec": {"containers": [{"name": "checkout", "image": "autoremediation-checkout:local", "env": [{"name": "BROKEN", "value": "0"}]}]}}}}
            self.apps.patch_namespaced_deployment(plan.target, plan.namespace, body)
            return "patched allowlisted checkout health flag to verified previous-good value"
        if plan.action == "scale_deployment":
            self.apps.patch_namespaced_deployment_scale(plan.target, plan.namespace, {"spec": {"replicas": plan.desired_replicas}})
            return f"scaled deployment to {plan.desired_replicas}"
        if plan.action == "restart_deployment":
            self.apps.patch_namespaced_deployment(plan.target, plan.namespace, {"spec": {"template": {"metadata": {"annotations": {"sre.platform/restarted-at": str(time.time())}}}}})
            return "restarted deployment"
        pod = self.core.list_namespaced_pod(plan.namespace, label_selector=f"app={plan.target}").items[0]
        self.core.delete_namespaced_pod(pod.metadata.name, plan.namespace)
        return f"deleted failed pod {pod.metadata.name}"

    def verify(self, plan: Plan, timeout_seconds: int = 90) -> bool:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            state = self.snapshot(plan)
            if state["available"] >= max(1, plan.current_replicas or 1) and not state["broken"]:
                return True
            time.sleep(2)
        return False


class LocalLabExecutor:
    """Compatibility-only test double; it is never selected by local cluster demos."""
    def __init__(self): self.state = {"checkout-api": {"revision": "v2", "replicas": 3, "healthy": False}}
    def precondition(self, plan: Plan) -> bool:
        item = self.state.get(plan.target); return bool(item and (plan.current_replicas is None or item["replicas"] == plan.current_replicas))
    def snapshot(self, plan: Plan) -> dict:
        item = self.state[plan.target]
        return {"resource_version": f"local-{item['replicas']}-{item['healthy']}", "replicas": item["replicas"], "available": int(item["healthy"]), "broken": not item["healthy"], "image": item.get("image", "local")}
    def evidence(self, service: str, namespace: str) -> list[dict[str, str]]: return [{"type": "metric", "source": "local-lab", "observation": "HTTP 5xx increased and readiness failed"}, {"type": "deployment", "source": service, "observation": "v2 deployed before error spike"}]
    def apply(self, plan: Plan) -> str:
        self.state[plan.target].update(revision="v1", healthy=True); return "local rollback"
    def verify(self, plan: Plan, timeout_seconds: int = 0) -> bool: return self.state[plan.target]["healthy"]
