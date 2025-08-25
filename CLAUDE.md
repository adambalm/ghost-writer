# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## PROJECT OVERVIEW

Ghost Writer: OCR and document processing system for handwritten notes.

**COMMERCIAL LICENSING REQUIREMENT**: This system is intended as a component of a commercial product. All dependencies must be compatible with commercial licensing. No GPL, AGPL, or other copyleft licenses that could create licensing restrictions for commercial use.

## DEVELOPMENT PROTOCOLS

1. **Evidence & Labeling**  
   - Tag claims as [verified] (with sources/specs) or [inference] (reasoned but unverified)
   - Provide source citations for technical decisions
   - Challenge proposals: "Why this approach?", "What's the evidence?", "Where could this fail?"

2. **Quality Assurance**
   - Run tests before committing changes
   - Validate fixes address root causes
   - Follow existing code patterns and conventions

3. **Professional Communication**
   - NEVER use exclamation points when announcing unverified results
   - NEVER claim something is "completely solved" or "fully working" until tested and confirmed
   - Avoid promotional/overhyped language - it is dangerous, not just stylistically bad
   - Suggest testing approaches and how to inspect results rather than declaring success
   - Act as a professional development partner, not a marketing department

## COMMANDS

**CRITICAL**: All Python commands MUST use the virtual environment. Never run Python without activating .venv first.

```bash
# ALWAYS activate virtual environment first
source .venv/bin/activate

# Run tests and generate reports  
python -m pytest tests/ -v --cov=src --cov-report=html

# Execute linting and type checking
ruff check src/ && mypy src/ --ignore-missing-imports

# Run filtered test suite (excluding Supernote tests)
pytest -q -k "not supernote and not e2e_supernote"

# For single-line execution (preferred)
source .venv/bin/activate && python -m pytest tests/ -v
```

## PYTHON ENVIRONMENT PROTOCOLS

### **MANDATORY Virtual Environment Usage**
1. **NEVER** run `python3` or `python` commands without activating .venv
2. **ALWAYS** use `source .venv/bin/activate && python` pattern
3. **ALL** Python scripts, tests, and development work MUST use .venv
4. **VERIFY** .venv activation before any Python operations

### **Virtual Environment Rules**
- **Location**: `.venv/` in project root (already configured)
- **Dependencies**: All project dependencies installed in .venv
- **Activation**: Required for ALL Python operations
- **Claude Code sessions**: Must activate .venv for any Python tool usage

### **Testing & Validation Protocols**
```bash
# ALWAYS test with virtual environment
source .venv/bin/activate && python test_script.py

# Verify imports before running complex operations
source .venv/bin/activate && python -c "import numpy, PIL, supernotelib; print('Dependencies OK')"

# Run project tests (filters out external test suites)
source .venv/bin/activate && python -m pytest tests/ -v

# Validate Supernote decoder against real files
source .venv/bin/activate && python parallel_extraction_test.py
```

### **Development Dependencies Status**
- **numpy**: ✅ Image/array processing
- **PIL (Pillow)**: ✅ Image manipulation  
- **supernotelib**: ✅ Reference implementation (licensing risk)
- **pytest**: ✅ Test framework
- **coverage**: ✅ Test coverage reporting
- **mypy, ruff**: ✅ Type checking and linting

## ARCHITECTURE

### Core Components:
- **Unified OCR Pipeline**: Qwen2.5-VL (primary) + Tesseract + Google Vision + GPT-4 Vision with intelligent routing
- **Local Vision Models**: Qwen2.5-VL 7B via Ollama for superior handwriting transcription (now unified across CLI and Web)
- **Relationship Detection**: Visual and semantic relationship analysis between note elements  
- **Concept Clustering**: Multi-strategy concept extraction and thematic organization
- **Structure Generation**: Multiple document formats (outline, mindmap, timeline, process)
- **Cost Controls**: Daily budget limits with automatic fallbacks

### Current Dependencies:
- **sn2md/supernotelib**: Used for .note file extraction [**LICENSING RISK**]
  - Status: External dependency for Supernote file parsing
  - Risk: Potential licensing conflicts for commercial use
  - Priority: **HIGH** - Must develop independent extraction capability

## CURRENT STATUS

- Test suite: **137 tests passing** ✅ 
- Test coverage: **76%** (exceeds 65% requirement) ✅
- OCR integration: Working with Tesseract 5.3.4 + Qwen2.5-VL + cloud providers
- Environment: Ubuntu 24.04, Python 3.12.3
- CI/CD: Enterprise Production Pipeline configured ✅
- Branch protection: Active with required status checks ✅
- MyPy compliance: **100%** (0 errors) ✅

## GIT WORKFLOW

1. **Branch Management**:
   - Work on feature branches: `feat/description`, `fix/description`, `chore/description`
   - Keep main branch clean and deployable
   - Delete feature branches after merging to avoid clutter
   - Always specify target branch: `git push origin branch-name`

2. **Standard Workflow**:
   ```bash
   # Create feature branch from main
   git checkout main && git pull origin main
   git checkout -b feat/new-feature
   
   # Work and commit changes
   git add . && git commit -m "feat: description"
   
   # Push to remote feature branch
   git push origin feat/new-feature
   
   # Create PR to main, then after merge:
   git checkout main && git pull origin main
   git branch -d feat/new-feature
   git push origin --delete feat/new-feature
   ```

3. **Never use bare `git push`** - always specify `git push origin <branch-name>`

## COMMIT POLICY

1. **File limits**: Max 7 files per commit, 300 lines diff (use multiple commits for larger changes)
2. **Commit body must include**: 
   - RISK: (assessment of change risk)
   - ROLLBACK: (how to undo if needed)
   - EVIDENCE: (path to test results in .handoff/)

## REPOSITORY ORGANIZATION

- **scripts/**: Utility scripts for testing and debugging Supernote integration
- **docs/**: All documentation organized by category (setup, development, api)
- **src/**: Source code organized by functionality
- **tests/**: Test suite with clear naming and coverage

## SECURITY REQUIREMENTS

- Never commit hardcoded credentials
- Use environment variables for sensitive configuration
- Include timeouts on all HTTP requests
- Validate input parameters and handle edge cases

## WORKING WITH OTHER AGENTS

- **AGENTS.md**: Used by OpenAI Codex for context and coordination
- **CLAUDE.md**: Used by Claude Code (this file) for development protocols
- Both files should be kept current and reflect actual repository status
