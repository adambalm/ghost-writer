# Claude Handoff — ghost-writer

## Branch
`ocr-mock-patch`

## Summary of work done
- Restored `tests/test_ocr_mocks.py` from backup due to broken `@pytest.mark.xfail` insertion.
- Fixed incorrect patch target from `src.utils.database.DatabaseManager` → `src.utils.ocr_providers.DatabaseManager`.
- All OCR mock tests now pass (`pytest -q tests/test_ocr_mocks.py` → 10 passed, 2 warnings).
- **Key insight:** `HybridOCR._get_provider_priority` includes `tesseract`, `google_vision`, and `gpt4_vision` when configured — but scoring branch for `gpt4_vision` exists only if env vars are set. Currently env-gated and mocked.

## State now
- **Mock-first**: No external Google/OpenAI calls. Tesseract local is fine.
- **Budget**: Later, do one-call smoke per provider only if env vars exist.
- **Patching**: Mock DB as `src.utils.ocr_providers.DatabaseManager`.

## Next tasks (in order)
1. Make `tests/test_structure_generation.py` pass.
2. Add one **E2E mocked pipeline**: OCR(mock) → relationships → concepts → structure.
3. Add **skipped API smoke tests** gated by `GOOGLE_APPLICATION_CREDENTIALS` and `OPENAI_API_KEY`.
4. Add ADR: `ADRs/ADR-0003-mock-first-ocr-routing.md`.
5. Append to `.agent_ledger.json` and `DECISION_HISTORY.md`.

## How to resume
```bash
source venv/bin/activate
pytest -q tests/test_structure_generation.py
```

## Notes / gotchas
- `HybridOCR._get_provider_priority` includes `gpt4_vision` when configured; scoring branches exist. Keep it mocked unless env-gated.
- Cost tracking occurs inside the hybrid loop; mocks now cover the selected-provider path.

## Pointers
- DECISION_HISTORY.md
- PRODUCT_SPECIFICATION.md
- TESTING_STRATEGY.md
- .agent_ledger.json
