#!/usr/bin/env bash
set -euo pipefail
E10_ISAAC_ROOT="${E10_ISAAC_ROOT:-/home/a/isaacsim}"
E10_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "${E10_ISAAC_ROOT}/isaac-sim.sh" --/app/settings/persistent=false \
    --exec "${E10_REPO_ROOT}/scripts/open_world.py"
