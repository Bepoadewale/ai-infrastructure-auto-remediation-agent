#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT/.local-validation"
mkdir -p "$LOG_DIR"
run_cycle() {
  local cycle="$1" log="$LOG_DIR/cleanroom-cycle-$1.log"
  (
    echo "clean-room cycle $cycle started $(date -u +%FT%TZ)"
    make -C "$ROOT" clean-local
    make -C "$ROOT" bootstrap-local
    make -C "$ROOT" smoke
    make -C "$ROOT" demo-rollback
    make -C "$ROOT" demo-remediation
    make -C "$ROOT" demo-image-recovery
    make -C "$ROOT" demo-stale-plan
    make -C "$ROOT" verify
    make -C "$ROOT" clean-local
    ! kind get clusters | grep -qx ai-sre-remediation
    echo "clean-room cycle $cycle complete $(date -u +%FT%TZ)"
  ) 2>&1 | tee "$log"
}
run_cycle 1
run_cycle 2
