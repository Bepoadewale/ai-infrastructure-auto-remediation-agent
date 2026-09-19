# Safety model

AI reasoning is advisory. Investigation is read-only and typed; remediation can only select a capability from the catalog. Policy fails closed, production writes require a different approver, plans are revalidated immediately before mutation, and execution success is not recovery until verification succeeds. Unknown actions, arbitrary commands, namespace deletion, persistent-data deletion and cluster-admin behavior are outside the capability catalog.
