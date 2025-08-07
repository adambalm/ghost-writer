# Ghost Writer v1.0 – Creative Scaffold MVP Specification

**Version**: 1.0  
**Date**: 2025-08-07  
**Authors**: MIT CMS Capstone Candidate  
**Status**: INTERNAL – REVISION FOR FINAL REVIEW

---

## EXECUTIVE SUMMARY

Ghost Writer is a focused, local-first toolkit that transforms handwritten Supernote drafts into structured digital artifacts and provides basic AI-assisted expansion. This MVP narrows the project scope to two core capabilities:

1. **OCR Ingestion & Archival** – reliably convert notes to text and store them with semantic indexing
2. **Style-Conditioned Expansion** – generate initial draft passages from archived note fragments, preserving authorial voice

All features target a single user persona: an author-researcher who maintains a personal archive of handwritten notes and seeks automated support for initial draft creation.

## SCOPE & SCOPE CONSTRAINTS

### In-Scope:
- **FR-001**: OCR ingestion of .note and PNG exports
- **FR-002**: Storage in SQLite with FAISS semantic index
- **FR-003**: Local LLM expansion of note fragments with style conditioning
- Test plan and evaluation metrics for OCR accuracy, style coherence, and draft utility

### Out-of-Scope:
- Automated publication to CMS or Git
- Multi-user or collaborative workflows
- Metaphysical "self-reconstruction" claims
- Agent-based orchestration frameworks

## USER PROFILE

**Persona**: Solo author and researcher, comfortable with command-line tools, values privacy and local control.

**Primary Goal**: Generate first-pass draft content from handwritten notes, reducing manual transcription and warm-up writing overhead.

## DATA SCHEMA & STORAGE

**Database**: SQLite

| Table | Columns |
|-------|---------|
| `notes` | `note_id TEXT PRIMARY KEY`, `source_file TEXT`, `raw_text TEXT`, `clean_text TEXT`, `created_at TIMESTAMP` |
| `embeddings` | `note_id TEXT`, `vector BLOB`, `FOREIGN KEY(note_id) REFERENCES notes(note_id)` |
| `expansions` | `expansion_id TEXT PRIMARY KEY`, `note_id TEXT`, `prompt TEXT`, `output TEXT`, `created_at TIMESTAMP` |

**Versioning**: Each `clean_text` and `output` record stores a timestamp; all inputs/outputs are immutable.

## FUNCTIONAL REQUIREMENTS

### FR-001: OCR Ingestion

**Trigger**: `ingest.py` reads new .note or PNG files in a watched folder.

**Behavior**:
- Extract raw text via Tesseract with layout preprocessing
- Store `raw_text` and initial `clean_text` (post-whitespace cleanup)
- Record ingestion errors to an `errors.log` with retry logic

**Performance**: ≤30 seconds per note on average hardware.

### FR-002: Archival & Semantic Indexing

**Storage**: Notes table as defined above.

**Embeddings**: Compute 768-dim vectors via sentence-transformers for each `clean_text`.

**Index**: Insert into FAISS index on disk.

**Search CLI**: `query.py --text "keyword"` returns top 5 `note_ids` with similarity scores.

**Error Handling**: If embedding fails, log and skip; ingestion continues.

### FR-003: Style-Conditioned Expansion

**Input**: `develop.py --note_id <id> --prompt "Expand"`

**Process**:
1. Load `clean_text` from notes
2. Prepend style context from a small corpus of 5 prior examples stored in `style_corpus/`
3. Invoke Ollama local LLM (LLaMA 3) with fixed prompt template
4. Save output to expansions table

**Quality Control**: Reject outputs exceeding 5% repetition rate; require manual override.

## TECHNICAL DEPENDENCIES

### Required Python Libraries:
- `tesseract-python` - OCR processing
- `sentence-transformers` - Text embeddings
- `faiss-cpu` - Vector similarity search
- `ollama-python` - Local LLM integration
- `sqlite3` - Database (Python standard library)

### Python Version: 3.9+

### Supernote Input Format:
- Primary: `.note` files from Supernote exports
- Fallback: PNG images converted to text
- Expected handwriting: Clear, structured notes with basic layout

### Style Corpus Bootstrapping:
- User provides 3-5 sample writing examples in `style_corpus/`
- System analyzes style patterns for consistent voice matching
- Optional: Import from existing blog posts or documents

## EVALUATION & TEST PLAN

| Metric | Target | Method |
|--------|--------|--------|
| **OCR Character Accuracy** | ≥85% | Compare 10 sample notes (ground truth) via `ocr_eval.py` |
| **Style Coherence Rating** | ≥4/5 (Likert scale) | 5 expert reviews of 10 expansions, average score ≥4 |
| **Draft Utility** | ≥3/5 (Likert scale) | 5 mock tasks: authors rate usefulness of 10 generated drafts |
| **System Robustness** | ≥90% completion rate | Ingest and expand 20 notes end-to-end without fatal errors |

### Evaluation Procedure:
1. Prepare a test suite of 10 diverse handwritten notes
2. Run `ingest.py` and record OCR accuracy metrics
3. Run `develop.py` on 10 selected fragments; collect LLM outputs
4. Have 3-5 reviewers rate each output on coherence, style match, and utility
5. Analyze results; document findings in `evaluation_report.md`

## ERROR BOUNDARIES & REPRODUCIBILITY

**Error Log**: All ingestion, embedding, expansion errors logged with timestamps.

**Immutable Records**: Raw and cleaned text, embeddings, and outputs are never overwritten.

**Reproduce Run**: Tag each run with a UUID; CLI flags `--run_id` to replicate processing pipeline.

## MVP ROADMAP

| Phase | Deliverables | Duration |
|-------|-------------|----------|
| **Phase 1** | Ingestion + OCR + Archival + Index | 2 weeks |
| **Phase 2** | CLI Search + Expansion Engine | 2 weeks |
| **Phase 3** | Evaluation Suite + Report | 1 week |

**Total Duration**: 5 weeks

## CLI INTERFACE DESIGN

### Core Commands:
```bash
# Ingest new notes
python ingest.py --input_dir=/path/to/notes --watch

# Search archived notes  
python query.py --text "keyword" --limit=5

# Expand note fragment
python develop.py --note_id=abc123 --prompt="Expand this into a blog post"

# Evaluate system performance
python evaluate.py --test_suite=validation_notes/
```

### Configuration:
- `config.yaml` for paths, model settings, style corpus location
- Environment variables for sensitive settings
- CLI help with `--help` flag for all commands

## NEXT STEPS

1. Finalize CLI prototypes and DB schema
2. Implement OCR ingestion with error logging
3. Build and verify FAISS index + search CLI
4. Integrate LLM expansion with style context
5. Execute evaluation plan and iterate

---

**Document Status**: Ready for implementation - Specification approved for Phase 1 development

**Next Review**: Post-Phase 1 evaluation and Phase 2 planning

This specification has removed all overreach, focuses on a single user profile, defines a concrete evaluation plan, and limits scope for a successful capstone project.