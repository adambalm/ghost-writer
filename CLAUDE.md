# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## PROJECT OVERVIEW

Ghost Writer: OCR and document processing system for handwritten notes.

## DEVELOPMENT PROTOCOLS

1. **Evidence & Labeling**  
   - Tag claims as [verified] (with sources/specs) or [inference] (reasoned but unverified)
   - Provide source citations for technical decisions
   - Challenge proposals: "Why this approach?", "What's the evidence?", "Where could this fail?"

2. **Quality Assurance**
   - Run tests before committing changes
   - Validate fixes address root causes
   - Follow existing code patterns and conventions

## COMMANDS

```bash
# Run tests and generate reports
python -m pytest tests/ -v --cov=src --cov-report=html

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

- Test suite: 112 passed, 7 failing, 23 deselected
- OCR integration: Working with Tesseract 5.3.4
- Environment: Ubuntu 24.04, Python 3.12.3
# Commit policy
# 1) Max 7 files per commit, 300 lines diff (use multiple commits).
# 2) Commit body must include: RISK:, ROLLBACK:, EVIDENCE: path(s) in .handoff/.
