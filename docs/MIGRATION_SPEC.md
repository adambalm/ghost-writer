# Ghost Writer Web Application Migration Specification

**Document Version**: 1.1  
**Purpose**: Autonomous execution plan and handoff documentation  
**Scope**: Migrate from scattered entrypoints to unified architecture  
**Constraints**: No sudo, no external network, explicit phase gates

---

## RESUMPTION PREFACE (How to Resume Next Session)

**Step 1**: Run read-only validation suite (Blocks A-G) to assess current state
**Step 2**: Post summarized results + any anomalies found  
**Step 3**: Request user authorization for Phase 2.1 (bytecode cleanup) if validation shows contamination

This prevents accidental drift when resuming with missing context.

---

## 1. CURRENT STATE ASSESSMENT

### 1.1 Infrastructure Status
- **Caddy proxy**: Active, routes `/enhanced/*` → 5001, `/*` → 8001
- **Python environment**: 3.12.3 via `./.venv/bin/python`
- **Port availability**: 5001/8001 disconnected (expected)

### 1.2 Contamination Analysis
- **Bytecode pollution**: `src/web/__pycache__/` contains:
  - `unified_app.cpython-312.pyc` → `/home/ed/ghost-writer/tests/../src/web/unified_app.py`
  - `__init__.cpython-312.pyc` → `/home/ed/ghost-writer/src/web/__init__.py`
- **Legacy entrypoints**: `archive/scattered-test-files/{enhanced_web_viewer.py, web_viewer_demo.py}`
- **Runtime template generation**: `enhanced_web_viewer.py:713` writes HTML at startup
- **Hardcoded paths**: Multiple `/home/ed/ghost-writer` references in legacy code

---

## 2. CLEANUP PROCEDURES (Phase 2.1 - DESTRUCTIVE)

### 2.1.1 Bytecode Elimination
**REQUIRES USER AUTHORIZATION - DESTRUCTIVE OPERATIONS**
```bash
# Remove all compiled Python artifacts
find src -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
find src -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
```

### 2.1.2 Verification (Read-Only)
```bash
# Confirm cleanup success
echo "=== Cleanup Verification ==="
find src -name "*.pyc" -o -name "__pycache__" | wc -l  # Must output: 0
grep -r "/home/ed" src/ 2>/dev/null && echo "❌ Still contaminated" || echo "✅ Clean"
```
**SUCCESS CRITERIA**: Both commands show 0 and "✅ Clean"

### 2.1.3 Prevention Guardrails  
**REQUIRES USER AUTHORIZATION - NON-DESTRUCTIVE WRITES**
```bash
# Session-level prevention
export PYTHONDONTWRITEBYTECODE=1

# Repository-level prevention (.gitignore modifications)
grep -q "__pycache__/" .gitignore || echo "__pycache__/" >> .gitignore
grep -q "*.pyc" .gitignore || echo "*.pyc" >> .gitignore
grep -q "*.pyo" .gitignore || echo "*.pyo" >> .gitignore
```

---

## 3. TARGET ARCHITECTURE

### 3.1 Directory Structure
```
src/web/
├── app.py              # Unified entrypoint (--mode enhanced|dev --port 5001|8001)
├── enhanced.py         # Enhanced viewer Blueprint  
├── dev.py             # Development viewer Blueprint
└── __init__.py        # Package marker

templates/
├── enhanced_index.html # Extracted static template (700+ lines)
├── simple_login.html   # Existing template (preserved)
└── demo_interface.html # Existing template (preserved)

scripts/
├── extract_template.py    # Template extraction utility
└── guardrails/
    └── check_writes.py     # Write path validator

Makefile               # Clean run targets: run-enhanced, run-dev, check, clean
RUNBOOK.md            # Operations guide
```

### 3.2 Policies (NON-NEGOTIABLE)

**Port Policy**:
- 5001: Enhanced mode only (`make run-enhanced`)
- 8001: Dev mode only (`make run-dev`)
- NO other ports permitted (including in comments)

**Write Path Policy**:
- ALLOWED: `uploads/`, `results/`, `sandbox/`, `scratch/`
- FORBIDDEN: `archive/`, `src/`, `templates/`, root level
- ENFORCEMENT: `scripts/guardrails/check_writes.py` with literal path checking

**Import Policy**:
- STANDARD: `from src.utils.X import Y`
- FORBIDDEN: `sys.path` manipulation, hardcoded absolute paths (including in comments)
- BASE_DIR: `Path(__file__).resolve().parents[2]` for file paths only

---

## 4. TEMPLATE EXTRACTION (Phase 4.1)

### 4.1.1 Python Method (NORMATIVE - ONLY METHOD)

**File**: `scripts/extract_template.py`
```python
#!/usr/bin/env python3
"""Template extractor: Find and extract embedded HTML template"""
import re
import sys
from pathlib import Path

def extract_template():
    """Extract enhanced_html template with sentinel-based detection"""
    source_file = Path("archive/scattered-test-files/enhanced_web_viewer.py")
    target_file = Path("templates/enhanced_index.html")
    
    if not source_file.exists():
        print(f"❌ ERROR: Source file not found: {source_file}")
        return False
    
    try:
        content = source_file.read_text(encoding='utf-8')
        
        # Find template using symmetric sentinel pattern
        pattern = r"enhanced_html\s*=\s*(?:'''|\"\"\")(.*?)(?:'''|\"\"\")"
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            print("❌ ERROR: Template marker 'enhanced_html = '''...''' or \"\"\"...\"\"\" not found")
            return False
        
        template_content = match.group(1).strip()
        
        # Verify it's valid HTML
        if not template_content.startswith('<!DOCTYPE html>'):
            print("❌ ERROR: Extracted content doesn't start with DOCTYPE")
            return False
        
        # Count basic HTML tags for sanity
        tag_count = len(re.findall(r'<[^/!][^>]*>', template_content))
        if tag_count < 10:
            print(f"❌ ERROR: Too few HTML tags ({tag_count}), extraction likely failed")
            return False
        
        # Ensure target directory exists
        target_file.parent.mkdir(exist_ok=True)
        
        # Write extracted template
        target_file.write_text(template_content, encoding='utf-8')
        
        # Final verification
        line_count = len(template_content.splitlines())
        print(f"✅ Template extracted: {line_count} lines, {tag_count} tags → {target_file}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Extraction failed: {e}")
        return False

if __name__ == '__main__':
    success = extract_template()
    sys.exit(0 if success else 1)
```

**Invocation**: `PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python scripts/extract_template.py`

---

## 5. GUARDRAILS IMPLEMENTATION

### 5.1 Write Path Validator

**File**: `scripts/guardrails/check_writes.py`
```python
#!/usr/bin/env python3
"""Enhanced Guardrails: Comprehensive write path validation with allowlist enforcement"""
import ast
import re
import sys
from pathlib import Path, PurePath

# Forbidden absolute path patterns (including in comments)
FORBIDDEN_PATH_PATTERNS = [
    r'/home/[^"\']*',     # Any /home/user path
    r'/tmp/[^"\']*',      # Any /tmp path  
    r'/var/[^"\']*',      # Any /var path
    r'/usr/[^"\']*',      # Any /usr path
    r'/etc/[^"\']*',      # Any /etc path
]

# Allowed write directories (relative to repo root)
ALLOWED_WRITE_DIRS = {'uploads', 'results', 'sandbox', 'scratch'}

class WriteAnalyzer(ast.NodeVisitor):
    """AST visitor to detect write operations with allowlist enforcement"""
    
    def __init__(self, file_path, repo_root):
        self.file_path = file_path
        self.repo_root = repo_root
        self.violations = []
    
    def visit_Call(self, node):
        """Check function/method calls for write operations"""
        
        # Built-in open() function
        if hasattr(node.func, 'id') and node.func.id == 'open':
            self._check_open_call(node)
        
        # Path.open() method
        elif (hasattr(node.func, 'attr') and node.func.attr == 'open'):
            self._check_path_open_call(node)
        
        # write_text/write_bytes methods
        elif hasattr(node.func, 'attr') and node.func.attr in ['write_text', 'write_bytes']:
            self._check_path_write_call(node)
        
        # mkdir operations (enhanced detection)
        elif hasattr(node.func, 'attr') and node.func.attr == 'mkdir':
            self._check_mkdir_call(node)
        
        # File object write operations
        elif hasattr(node.func, 'attr') and node.func.attr in ['write', 'writelines']:
            self.violations.append(f"{self.file_path}:{node.lineno}: File write operation detected")
        
        self.generic_visit(node)
    
    def _check_open_call(self, node):
        """Analyze open() function calls with allowlist checking"""
        write_mode = False
        path_arg = None
        
        # Check positional arguments
        if len(node.args) >= 1:
            path_arg = node.args[0]
        if len(node.args) >= 2:
            mode_node = node.args[1]
            if isinstance(mode_node, ast.Constant) and isinstance(mode_node.value, str):
                if any(m in mode_node.value for m in ['w', 'a', 'x']):
                    write_mode = True
        
        # Check keyword mode argument
        for keyword in node.keywords:
            if keyword.arg == 'mode' and isinstance(keyword.value, ast.Constant):
                if any(m in keyword.value.value for m in ['w', 'a', 'x']):
                    write_mode = True
        
        if write_mode:
            violation = f"{self.file_path}:{node.lineno}: open() with write mode"
            if path_arg and isinstance(path_arg, ast.Constant):
                if not self._check_allowed_path(path_arg.value):
                    violation += f" to forbidden path: {path_arg.value}"
            self.violations.append(violation)
    
    def _check_path_open_call(self, node):
        """Analyze Path.open() method calls"""
        if len(node.args) >= 1:
            mode_node = node.args[0]
            if isinstance(mode_node, ast.Constant) and isinstance(mode_node.value, str):
                if any(m in mode_node.value for m in ['w', 'a', 'x']):
                    self.violations.append(f"{self.file_path}:{node.lineno}: Path.open() with write mode '{mode_node.value}'")
    
    def _check_path_write_call(self, node):
        """Analyze Path.write_text/write_bytes calls"""
        self.violations.append(f"{self.file_path}:{node.lineno}: Path write operation '{node.func.attr}'")
    
    def _check_mkdir_call(self, node):
        """Analyze mkdir operations with enhanced Path(...).mkdir detection"""
        path_literal = None
        
        # Check if this is a method call on a Path object
        if hasattr(node.func, 'value'):
            # Case: Path("literal").mkdir(...)
            if (isinstance(node.func.value, ast.Call) and 
                hasattr(node.func.value.func, 'id') and 
                node.func.value.func.id == 'Path' and
                len(node.func.value.args) >= 1 and
                isinstance(node.func.value.args[0], ast.Constant)):
                path_literal = node.func.value.args[0].value
            
            # Case: existing_path_var.mkdir(...)
            elif isinstance(node.func.value, ast.Constant):
                path_literal = str(node.func.value.value)
        
        if path_literal:
            if not self._check_allowed_path(path_literal):
                self.violations.append(f"{self.file_path}:{node.lineno}: mkdir to forbidden path: {path_literal}")
        else:
            self.violations.append(f"{self.file_path}:{node.lineno}: mkdir operation (verify target directory)")
    
    def _check_allowed_path(self, path_str):
        """Check if literal path is under allowed write directories"""
        try:
            if isinstance(path_str, str):
                path = Path(path_str)
                if path.is_absolute():
                    # Absolute paths must be under repo_root/allowed_dir
                    try:
                        rel_path = path.relative_to(self.repo_root)
                        return rel_path.parts[0] in ALLOWED_WRITE_DIRS
                    except ValueError:
                        return False
                else:
                    # Relative paths: check if first component is allowed
                    return path.parts[0] in ALLOWED_WRITE_DIRS if path.parts else False
        except Exception:
            pass
        return False  # Conservative: unknown paths are forbidden

def check_hardcoded_paths(file_path, content):
    """Check for forbidden absolute paths in content (including comments)"""
    violations = []
    lines = content.splitlines()
    
    for line_num, line in enumerate(lines, 1):
        for pattern in FORBIDDEN_PATH_PATTERNS:
            matches = re.finditer(pattern, line)
            for match in matches:
                violations.append(f"{file_path}:{line_num}: Hardcoded path '{match.group().strip()}'")
    return violations

def check_write_operations(file_path, content, repo_root):
    """Check for write operations via AST analysis"""
    try:
        tree = ast.parse(content, filename=str(file_path))
        analyzer = WriteAnalyzer(file_path, repo_root)
        analyzer.visit(tree)
        return analyzer.violations
    except SyntaxError as e:
        return [f"{file_path}:{e.lineno}: Syntax error prevents analysis: {e.msg}"]

def main():
    """Main guardrails validation"""
    repo_root = Path(__file__).resolve().parents[2]
    web_dir = repo_root / 'src' / 'web'
    
    if not web_dir.exists():
        print("✅ PASS: src/web/ not found - guardrails pass vacuously")
        return 0
    
    violations = []
    file_count = 0
    
    for py_file in web_dir.glob('**/*.py'):
        file_count += 1
        try:
            content = py_file.read_text(encoding='utf-8')
            violations.extend(check_hardcoded_paths(py_file, content))
            violations.extend(check_write_operations(py_file, content, repo_root))
        except Exception as e:
            violations.append(f"{py_file}: Error reading file: {e}")
    
    print(f"Analyzed {file_count} Python files in src/web/")
    
    if violations:
        print(f"❌ FAIL: {len(violations)} guardrails violations found:")
        for violation in violations:
            print(f"  {violation}")
        return 1
    else:
        print("✅ PASS: No guardrails violations found")
        return 0

if __name__ == '__main__':
    sys.exit(main())
```

---

## 6. VALIDATION PROTOCOL

### Block A: Environment Check
```bash
echo "=== Environment Check ==="
./.venv/bin/python --version  # Must show "Python 3.12.3"
ls -la src/utils/ | head -5    # Must show ≥5 .py files
```
**✅ PASS**: Python 3.12.3 AND ≥5 utils files  
**❌ FAIL**: Version mismatch OR utils missing

### Block B: Code Quality (AST Syntax)
```bash
echo "=== Code Quality (AST) ==="
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python - <<'PY'
import sys, ast
from pathlib import Path

base = Path("src/web")
py_files = sorted(p for p in base.rglob("*.py"))
if not py_files:
    print("INFO: No Python files found under src/web (expected if artifacts not yet materialized).")
    sys.exit(0)

errors = 0
for p in py_files:
    try:
        src = p.read_text(encoding="utf-8")
        ast.parse(src, filename=str(p))
    except SyntaxError as e:
        errors = 1
        print(f"SyntaxError: {p}:{e.lineno}:{e.offset} {e.msg}")
    except Exception as e:
        errors = 1
        print(f"ERROR reading/parsing {p}: {e}")

if errors:
    sys.exit(1)
else:
    print("✓ Syntax OK (AST parse passed for all discovered files)")
PY
```
**✅ PASS**: "✓ Syntax OK (AST parse passed for all discovered files)"  
**❌ FAIL**: Any "SyntaxError:" or "ERROR reading/parsing"

### Block C: Path Hygiene (Including Comments)
```bash
echo "=== Path Hygiene ==="
if [ -d src/web ]; then
  grep -nR "/home/ed\|/tmp/\|/var/" src/web || echo "✅ No hardcoded paths"
else
  echo "INFO: src/web absent; passes vacuously"
fi
```
**✅ PASS**: "✅ No hardcoded paths" OR "INFO: src/web absent"  
**❌ FAIL**: ANY `/home/ed`, `/tmp/`, `/var/` output (including in comments)

### Block D: Template References
```bash
echo "=== Template References ==="
# Enhanced blueprint must reference enhanced_index.html
if [ -f src/web/enhanced.py ]; then
  grep -q "enhanced_index.html" src/web/enhanced.py || echo "❌ Missing enhanced_index.html ref"
fi
# Dev blueprint must reference demo_interface.html  
if [ -f src/web/dev.py ]; then
  grep -q "demo_interface.html" src/web/dev.py || echo "❌ Missing demo_interface.html ref"
fi
# All referenced templates must exist
ls -la templates/enhanced_index.html templates/demo_interface.html templates/simple_login.html 2>/dev/null || echo "INFO: Templates not found"
```
**✅ PASS**: All expected template files exist AND referenced in correct blueprints  
**❌ FAIL**: Missing template file OR wrong blueprint reference

### Block E: Import Dependencies
```bash
echo "=== Import Dependencies ==="
if [ -d src/web ]; then
  grep -rh "from src\.utils\." src/web/ | head -10 || echo "INFO: No src.utils imports found"
fi
ls src/utils/*.py 2>/dev/null | wc -l || echo "INFO: src/utils missing"
```
**✅ PASS**: All `src.utils.X` imports have corresponding files  
**❌ FAIL**: Import references non-existent module

### Block F: Write Path Validation
```bash
echo "=== Write Path Validation ==="
if [ -f scripts/guardrails/check_writes.py ]; then
  PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python scripts/guardrails/check_writes.py
else
  echo "INFO: Guardrails script not found"
fi
```
**✅ PASS**: "✅ PASS: No guardrails violations found"  
**❌ FAIL**: Any violations reported

### Block G: Port Configuration (Including Comments)
```bash
echo "=== Port Configuration ==="
if [ -d src/web ]; then
  grep -rn "port.*[0-9]" src/web/ | grep -v "5001\|8001" && echo "❌ Forbidden ports found" || echo "✅ Only 5001/8001"
else
  echo "INFO: src/web absent; passes vacuously"
fi
```
**✅ PASS**: "✅ Only 5001/8001" OR "INFO: src/web absent"  
**❌ FAIL**: References to ports other than 5001/8001 (including in comments)

---

## 7. FUNCTIONAL TESTING (Phase 7.1)

### 7.1.1 Health Endpoint Test (Timeout Fallback Included)
```bash
echo "=== Functional Test (Python-only with timeout fallback) ==="

# Start app with timeout fallback
if command -v timeout >/dev/null 2>&1; then
  PYTHONDONTWRITEBYTECODE=1 timeout 30s ./.venv/bin/python src/web/app.py --mode dev --port 8001 &
else
  # Fallback for systems without timeout command
  PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python src/web/app.py --mode dev --port 8001 &
fi
APP_PID=$!

# Wait for startup (max 10 seconds, no bc dependency)
echo "Waiting for app startup..."
for i in {1..20}; do
  if curl -s http://127.0.0.1:8001/healthz >/dev/null 2>&1; then
    echo "App responding after ${i} polls ($(($i / 2))s)"
    break
  fi
  sleep 0.5
done

# Capture response
RESPONSE=$(curl -s http://127.0.0.1:8001/healthz 2>/dev/null || echo "CURL_FAILED")
kill $APP_PID 2>/dev/null || true
wait $APP_PID 2>/dev/null || true

# Validate with Python (no jq dependency)
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python - <<PY
import json, sys
try:
    response = """$RESPONSE"""
    if response == "CURL_FAILED":
        print("❌ FAIL: Could not reach health endpoint")
        sys.exit(1)
    
    data = json.loads(response)
    
    # Required fields and types
    if data.get("status") != "ok":
        print(f"❌ FAIL: status != 'ok', got: {data.get('status')}")
        sys.exit(1)
    
    if data.get("mode") != "dev":
        print(f"❌ FAIL: mode != 'dev', got: {data.get('mode')}")
        sys.exit(1)
    
    if not isinstance(data.get("pid"), int):
        print(f"❌ FAIL: pid not integer, got: {type(data.get('pid'))}")
        sys.exit(1)
    
    if not isinstance(data.get("base_dir"), str) or "/ghost-writer" not in data.get("base_dir"):
        print(f"❌ FAIL: base_dir invalid, got: {data.get('base_dir')}")
        sys.exit(1)
    
    print("✅ PASS: Functional test passed")
    print(f"  Status: {data['status']}, Mode: {data['mode']}, PID: {data['pid']}")
    
except json.JSONDecodeError as e:
    print(f"❌ FAIL: Invalid JSON response: {e}")
    print(f"  Response: {response}")
    sys.exit(1)
except Exception as e:
    print(f"❌ FAIL: Validation error: {e}")
    sys.exit(1)
PY
```

**Expected JSON**: `{"status":"ok","mode":"dev","pid":12345,"base_dir":"/path/to/ghost-writer"}`  
**✅ PASS**: All JSON fields present with correct types  
**❌ FAIL**: Missing fields, wrong types, or connection failure

---

## 8. EXECUTION CONSTRAINTS

### 8.1 Safety Boundaries
- **NO SUDO**: Never use `sudo`, `systemctl --system`, or `/etc` modifications
- **NO EXTERNAL NETWORK**: Only localhost (`127.0.0.1`) connections permitted
- **NO PACKAGE INSTALLATION**: Use existing `.venv` only

### 8.2 Consensus Requirements
- **NO COMMAND EXECUTION** without both assistants explicitly agreeing
- **PARAPHRASE PROTOCOL**: Receiving assistant must paraphrase; sender must correct until convergence
- **PHASE GATES**: User authorization required for destructive operations

### 8.3 Rollback Strategy
```bash
# Emergency rollback (if migration fails)
git checkout HEAD -- src/web/
rm -rf uploads/ results/ sandbox/ scratch/ scripts/extract_template.py scripts/guardrails/
git status  # Verify clean working tree
```

---

## 9. EXECUTION PHASE GATES

### Phase 2.1: Bytecode Cleanup
**AUTHORIZATION REQUIRED** - Destructive file deletion
- Commands: `find src -name "__pycache__" -exec rm -rf {} +`, `.gitignore` updates
- Risk: Irreversible removal of compiled artifacts
- Verification: Zero `.pyc` files remain

### Phase 4.1: Template Extraction  
**AUTHORIZATION REQUIRED** - File creation in `templates/`
- Command: `PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python scripts/extract_template.py`
- Risk: Overwrites existing `templates/enhanced_index.html`
- Verification: Valid HTML with DOCTYPE

### Phase 5.1-5.3: File Materialization
**AUTHORIZATION REQUIRED** - Multiple file creation
- Commands: Writing `src/web/*.py`, `Makefile`, guardrails
- Risk: Conflicts with existing files
- Verification: All validation blocks pass

### Phase 7.1: Functional Testing
**AUTHORIZATION REQUIRED** - Service startup on ports 5001/8001
- Commands: App startup + health endpoint test
- Risk: Port binding conflicts
- Verification: Clean health response + graceful shutdown

**END OF SPECIFICATION**