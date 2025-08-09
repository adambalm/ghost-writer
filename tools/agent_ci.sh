#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
mkdir -p .handoff
pytest -q --junitxml=.handoff/tests.xml || true
coverage run -m pytest -q || true
coverage xml -o .handoff/coverage.xml || true
ruff check . > .handoff/ruff.txt || true
mypy src > .handoff/mypy.txt || true
python - <<PY
from junitparser import JUnitXml
p=".handoff/tests.xml"
try:
  x=JUnitXml.fromfile(p); passed=sum(1 for s in x if all([t.result is None for t in s]))
  failed=sum(1 for s in x for t in s if t.result and t.result._tag==failure)
  errors=sum(1 for s in x for t in s if t.result and t.result._tag==error)
  skipped=sum(1 for s in x for t in s if t.result and t.result._tag==skipped)
  open(".handoff/summary.json","w").write(str({"passed":passed,"failed":failed,"errors":errors,"skipped":skipped}))
except Exception as e:
  open(".handoff/summary.json","w").write(str({"error":str(e)}))
PY
