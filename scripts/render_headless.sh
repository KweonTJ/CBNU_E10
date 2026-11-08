#!/usr/bin/env bash
set -euo pipefail
E10_ISAAC_ROOT="${E10_ISAAC_ROOT:-/home/a/isaacsim}"
E10_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "${E10_REPO_ROOT}/outputs/runtime"
exec "${E10_ISAAC_ROOT}/isaac-sim.sh" --no-window \
    --/app/window/width=1000 --/app/window/height=1300 \
    --/renderer/activeGpu=0 --/renderer/multiGpu/enabled=false \
    --/app/settings/persistent=false \
    --exec "${E10_REPO_ROOT}/scripts/capture_and_check.py" \
    > "${E10_REPO_ROOT}/outputs/runtime/isaac_capture.log" 2>&1
