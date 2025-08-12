# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## PROJECT OVERVIEW

Ghost Writer: OCR and document processing system for handwritten notes that transforms handwritten content into structured digital documents.

## DEVELOPMENT PROTOCOLS

1. **Evidence & Labeling**  
   - Tag claims as [verified] (with sources/specs) or [inference] (reasoned but unverified)
   - Provide source citations for technical decisions
   - Challenge proposals: "Why this approach?", "What's the evidence?", "Where could this fail?"

2. **Quality Assurance**
   - Run tests before committing changes
   - Validate fixes address root causes
   - Follow existing code patterns and conventions

3. **Repository Organization**
   - Keep root directory clean and professional
   - Move debug scripts to `scripts/` directory
   - Use `docs/` for all documentation
   - Delete obsolete files rather than accumulating cruft

## COMMANDS

```bash
# Run all tests with coverage
python -m pytest tests/ -v --cov=src --cov-report=html

# Run exact CI commands (matches GitHub Actions)
pytest --junitxml=.handoff/tests.xml -ra --strict-markers --strict-config

# Execute linting and type checking
ruff check src/ && mypy src/ --ignore-missing-imports

# Run filtered test suite (excluding Supernote tests)
pytest -q -k "not supernote and not e2e_supernote"
```

## ARCHITECTURE

### Core Components:
- **Hybrid OCR Pipeline**: Tesseract + Google Vision + GPT-4 Vision with intelligent routing
- **Relationship Detection**: Visual and semantic relationship analysis between note elements  
- **Concept Clustering**: Multi-strategy concept extraction and thematic organization
- **Structure Generation**: Multiple document formats (outline, mindmap, timeline, process)
- **Cost Controls**: Daily budget limits with automatic fallbacks

## CURRENT STATUS

- Test suite: **137 passed, 0 failing** ✅
- Test coverage: **70.45%** (exceeds 65% requirement) ✅
- OCR integration: Working with Tesseract 5.3.4
- Environment: Ubuntu 24.04, Python 3.12.3
- CI/CD: All GitHub Actions passing ✅
- Branch protection: Active with required status checks ✅

## COMMIT POLICY

1. **File limits**: Max 7 files per commit, 300 lines diff (use multiple commits for larger changes)
2. **Commit body must include**: 
   - RISK: (assessment of change risk)
   - ROLLBACK: (how to undo if needed)
   - EVIDENCE: (path to test results in .handoff/)

## SECURITY REQUIREMENTS

- Never commit hardcoded credentials
- Use environment variables for sensitive configuration
- Include timeouts on all HTTP requests
- Validate input parameters and handle edge cases

## DOCUMENTATION STANDARDS

- Keep README.md focused and under 50 lines
- Use `docs/` directory for detailed documentation
- Maintain `CLAUDE.md` (this file) for agent protocols
- Update `AGENTS.md` for Codex coordination

## WORKING WITH OTHER AGENTS

- **AGENTS.md**: Used by OpenAI Codex for context and coordination
- **CLAUDE.md**: Used by Claude Code (this file) for development protocols
- Both files should be kept current and reflect actual repository status