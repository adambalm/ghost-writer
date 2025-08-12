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

- Test suite: **137 passed, 0 failing** ✅
- Test coverage: **70.45%** (exceeds 65% requirement) ✅
- OCR integration: Working with Tesseract 5.3.4
- Environment: Ubuntu 24.04, Python 3.12.3
- CI/CD: All GitHub Actions passing ✅
- Branch protection: Active with required status checks ✅

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
