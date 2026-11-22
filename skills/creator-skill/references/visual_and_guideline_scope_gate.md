# Visual source and guideline-scope gate (Beta 1.16)

Use `scripts/evidence_reconciliation_gate.py` when an original PDF archive and a clinical claim register are available. This does **not** replace medical review.

1. Inspect every PDF in the original source archive, including image-only pages; a Markdown cartridge is not a substitute for the source diagrams, image text, clinical photos, ECG, tables, etc.
2. Mark a same-lesson additional PDF as `PENDING_SCOPE_SELECTION_IMAGE_ONLY` unless the user or evidence selects it. Do not silently exclude or silently merge it.
3. Verify original PDF hashes, full page manifest, and the selected-source list.
4. Compare relevant assertions against official guideline sections, distinguishing supported claims, conditional claims, contradictions, and unsupported specifics; retain original claims unchanged in an internal register.
5. A guideline link or a self-attested review is not independent medical approval. Keep `release_allowed=false` if clinical/visual review is pending.
6. Never add citations, the evidence register, or a reference section to the learner's PDF. Preserve it in private QA artifacts.

Example CLI:

```bash
python scripts/evidence_reconciliation_gate.py GUIDELINE_TRIAGE_BETA116.json ORIGINAL_PDF_VISUAL_MANIFEST_BETA116.json --source-archive original_sources.zip
```
