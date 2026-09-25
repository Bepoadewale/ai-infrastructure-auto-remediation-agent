#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
stop_port_forwards
if kind get clusters | grep -qx "$CLUSTER_NAME"; then kind delete cluster --name "$CLUSTER_NAME"; fi
rm -rf "$LOCAL_DIR"
echo "clean-local: removed only $CLUSTER_NAME and project .local state"
