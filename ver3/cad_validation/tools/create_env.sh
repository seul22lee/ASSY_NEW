#!/usr/bin/env bash
# Recreate the Ver3 CAD pilot environment at a caller-supplied path.
#
#   ver3/cad_validation/tools/create_env.sh <env_path> [python]
#
#   env_path   where the virtualenv is created. Required - this script never
#              picks a location for you and never writes to a temporary
#              directory of its own choosing.
#   python     interpreter to build it with. Defaults to python3.8.
#
# The environment is NOT committed. The lock file is. Anything reproducible
# about this pilot has to come from requirements-cad.txt, not from a directory
# that happened to survive on one machine.
set -euo pipefail

ENV_PATH="${1:-}"
PY="${2:-python3.8}"

if [[ -z "$ENV_PATH" ]]; then
    echo "usage: $0 <env_path> [python]" >&2
    exit 2
fi
if [[ -e "$ENV_PATH" ]]; then
    echo "error: $ENV_PATH already exists; refusing to overwrite" >&2
    exit 2
fi
if ! command -v "$PY" >/dev/null 2>&1; then
    echo "error: interpreter '$PY' not found." >&2
    echo "       cadquery-ocp 7.7.0 publishes cp38 wheels; the pinned set in" >&2
    echo "       requirements-cad.txt was verified only on CPython 3.8." >&2
    exit 2
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQ="$HERE/../requirements-cad.txt"

echo "creating $ENV_PATH with $PY"
# --without-pip then bootstrap: on the pilot host the bundled ensurepip was
# unusable, and bootstrapping is the path that was actually verified.
"$PY" -m venv --without-pip "$ENV_PATH"

if ! "$ENV_PATH/bin/python" -m pip --version >/dev/null 2>&1; then
    echo "bootstrapping pip"
    curl -fsSL https://bootstrap.pypa.io/pip/3.8/get-pip.py -o "$ENV_PATH/get-pip.py"
    "$ENV_PATH/bin/python" "$ENV_PATH/get-pip.py"
    rm -f "$ENV_PATH/get-pip.py"
fi

"$ENV_PATH/bin/python" -m pip install --no-cache-dir -r "$REQ"

echo "verifying"
"$ENV_PATH/bin/python" - <<'PY'
import cadquery as cq
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepTools import BRepTools
b = cq.Solid.makeBox(10, 10, 10)
assert BRepCheck_Analyzer(b.wrapped).IsValid(), "B-rep kernel produced an invalid solid"
print("cadquery", cq.__version__, "- B-rep kernel OK")
PY

echo
echo "environment ready: $ENV_PATH"
echo "run validation with: $ENV_PATH/bin/python <reference>/validate.py"
