from prometheus_client import Counter, Histogram

INCIDENTS = Counter("sre_remediation_incidents_total", "Incidents by lifecycle status", ["status"])
PLANS = Counter("sre_remediation_plans_total", "Plans by policy result", ["result"])
ACTIONS = Counter("sre_remediation_actions_total", "Bounded remediation actions", ["action", "result"])
VERIFY_SECONDS = Histogram("sre_remediation_verification_seconds", "Time spent verifying remediation")
