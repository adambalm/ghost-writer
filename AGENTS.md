# AGENTS.md

This file coordinates development efforts between different AI agents (primarily OpenAI Codex) working on the Ghost Writer repository.

---

## CURRENT STATUS

**Active Branch:** chore/ignore-handoff
**Test State:** 137 tests passing, 0 failures (100% pass rate)
**Coverage:** 70.45% overall code coverage
**CI Status:** All checks passing
**OCR Integration:** Working with Tesseract 5.3.4
**Environment:** Ubuntu 24.04, Python 3.12.3

---

## REPOSITORY STRUCTURE

Clean, organized structure:
- `scripts/` - Testing and debugging utilities for Supernote integration
- `docs/setup/` - Environment and installation guides
- `docs/development/` - Development processes, testing strategy, and decisions
- `docs/` - API documentation and specifications
- `src/` - Source code organized by functionality
- `tests/` - Comprehensive test suite with 137 passing tests

---

## CODEX COORDINATION PROTOCOLS

1. **Before Starting Work:**
   - Read CLAUDE.md for current development protocols and git workflow
   - Check CI status and test results in .handoff/tests.xml
   - Review recent commits for context

2. **Security Requirements:**
   - No hardcoded credentials or API keys in any files
   - Use environment variables for all secrets
   - Implement proper HTTP timeouts (30s default)
   - Follow principle of least privilege

3. **Testing Standards:**
   - All tests must pass before commits (currently 137/137 passing)
   - Run: `python -m pytest tests/ -v --cov=src --cov-report=html`
   - Target: Maintain >65% code coverage (currently 70.45%)

4. **Code Quality:**
   - Run linting: `ruff check src/`
   - Run type checking: `mypy src/ --ignore-missing-imports`
   - Follow existing code patterns and conventions

---

## RECENT ACHIEVEMENTS

- ✅ Resolved all failing tests (from 7 failures to 0)
- ✅ Fixed Supernote parser content detection with smart algorithms
- ✅ Cleaned CI workflow to eliminate duplicate coverage collection
- ✅ Fixed GitHub Repository Rules for branch protection
- ✅ Organized repository structure (moved scripts to scripts/, docs to docs/)
- ✅ Established git workflow protocols

---

## SUPERNOTE INTEGRATION TOOLS

Located in `scripts/` directory:
- `debug_supernote_test.py` - Detailed connection debugging with step-by-step verification
- `test_supernote_api.py` - API integration test using SupernoteCloudAPI classes
- `quick_supernote_test.py` - Quick connection test for users
- Additional utilities: `validate_supernote.py`, `final_supernote_test.py`, etc.

---

## DEVELOPMENT FOCUS AREAS

1. **OCR Pipeline Optimization:** Hybrid routing between Tesseract/Google Vision/GPT-4V
2. **Relationship Detection:** Visual and semantic analysis between note elements
3. **Concept Clustering:** Multi-strategy extraction and thematic organization
4. **Structure Generation:** Multiple output formats (outline, mindmap, timeline, process)
5. **Cost Controls:** Daily budget limits with automatic fallbacks

