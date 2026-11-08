#!/usr/bin/env bash
set -euo pipefail
E10_ISAAC_ROOT="${E10_ISAAC_ROOT:-/home/a/isaacsim}"
E10_USD_EXT=""
for E10_CANDIDATE in "${E10_ISAAC_ROOT}"/extscache/omni.usd.libs-*; do
    if [[ -d "${E10_CANDIDATE}/pxr" ]]; then
        E10_USD_EXT="${E10_CANDIDATE}"
        break
    fi
done
if [[ -z "${E10_USD_EXT}" ]]; then
    echo "Cannot find Isaac Sim USD Python under ${E10_ISAAC_ROOT}" >&2
    exit 1
fi
exec env PYTHONPATH="${E10_USD_EXT}${PYTHONPATH:+:${PYTHONPATH}}" \
    LD_LIBRARY_PATH="${E10_USD_EXT}/bin:${E10_ISAAC_ROOT}/kit${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}" \
    PXR_PLUGINPATH_NAME="${E10_USD_EXT}/bin/usd" \
    "${E10_ISAAC_ROOT}/kit/python/bin/python3" -B "$@"

