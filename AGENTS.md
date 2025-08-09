# AGENTS.md — Cross-Agent Handoff & Ledger

This file is a persistent, model-agnostic record of handoffs, context, and coordination between AI coding agents (e.g., Claude Code CLI, OpenAI Codex, ChatGPT).  
It ensures continuity of work across suspensions, restarts, and model switches.

---

## Purpose
- Maintain **state awareness** between different LLM agents.
- Provide **clear entry points** for resuming work.
- Capture **decisions, rationale, and current tasks** without relying on volatile context windows.

---

## Current Active Branch
fix/triage-pack-1

---

## Last Handoff
**From:** ChatGPT (Black Flag Protocol active)  
**To:** Claude Code CLI  
**Date:** 2025-08-08  
**Reference File:** CLAUDE_HANDOFF.md  

---

## Key Context
- Tests fixed for `test_confidence_based_provider_selection` via correct `patch` target.
- All tests now passing in `tests/test_ocr_mocks.py`.
- `HybridOCR._get_provider_priority` includes `gpt4_vision` branch; keep mocked unless env-gated.
- Cost tracking integrated inside hybrid loop.

---

## Next Steps (per last handoff)
1. Make `tests/test_structure_generation.py` pass.
2. Add mocked E2E pipeline: OCR(mock) → relationships → concepts → structure.
3. Add skipped API smoke tests gated by `GOOGLE_APPLICATION_CREDENTIALS` and `OPENAI_API_KEY`.
4. Add ADR: `ADRs/ADR-0003-mock-first-ocr-routing.md`.
5. Append to `.agent_ledger.json` and `DECISION_HISTORY.md`.

---

## Files to Always Check Before Resuming
- CLAUDE_HANDOFF.md  
- DECISION_HISTORY.md  
- PRODUCT_SPECIFICATION.md  
- TESTING_STRATEGY.md  
- .agent_ledger.json

