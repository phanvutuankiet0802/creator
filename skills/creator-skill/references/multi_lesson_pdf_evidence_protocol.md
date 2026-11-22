# Beta 1.21 — PDF-bound, cross-lesson assessment QA

**Scope:** Occupational / environmental health education. Apply to other PDF-grounded disciplines when a real selected PDF exists. This does **not** establish medical, legal or psychometric validation.

## Learning context first

1. Select **actual source provided by the user**, not a made-up environmental medicine prompt. In this benchmark, two independent sources were already provided: *Âm thanh và tiếng ồn trong sản xuất & Điếc nghề nghiệp* and *Tai nạn lao động*. Record lesson goals separately. Do not assume that their shared specialty makes the learning objectives interchangeable.
2. Noise source goals (page 2): concept of sound; sources and characteristics of workplace noise; occupational hearing loss; protection. Sample items may test definitions, units/frequency, exposure and duration, audiometry, risk control at source and PPE. Do not force all questions into emergency clinical vignettes.
3. Occupational accidents source goals (page 2): occupational injury risk factors, direct causal mechanisms, and prevention. Sample items should identify and distinguish environmental, technical, organizational and behavioral causes. Never substitute the noise lecture's occupational deafness taxonomy for accident-prevention learning goals.
4. Preserve claims as **source-derived**. When the same slides disagree, e.g. page 45 vs 63 of the noise source concerning minimum years of exposure, mark `HOLD_FOR_ACADEMIC_REVIEW`. Do not choose one number as an unquestioned answer. Review legal standards against current law separately before using them as correct-key anchors.
5. For each item, require an anchor to the **exact PDF page** and PDF SHA-256, not merely a matching sentence somewhere in extracted text. In Python-capable environments, invoke `scripts/pdf_page_grounding.py::audit_pdf_page_grounding(questions, pdf_sources)`. In `tao-de` the adaptive HTML builder accepts the optional `pdf_sources={source_id: actual_pdf_path}` parameter and blocks failed anchoring. If page image has no extractable text, inspect and ground visually; do not pretend OCR is complete.
6. For any critical reasoning-labelled item, evaluate whether a **changed decisive finding changes the preferred answer**. Reviewer must check if the suggested counterfactual is clinically/organizationally valid, not just that the two keys differ.
7. Run learner-visible HTML in a browser, click answers and verify explanation. Distinguish **source integrity**, **pedagogical fitness**, **distractor plausibility**, **calibrated difficulty**, **legal/clinical accuracy**. Structural PASS is not a release certificate.
8. Do not pad options merely for equal lengths. Reject strong answer-length cues, but do not impose an artificial 10% 'correct longest' quota. Explain why each distractor might be chosen, and label weak distractors in the internal QA board.
9. `creator-skill` acts as PM: if a supposedly 'hard' assessment has easily eliminated distractors, redirect to authoring before expanding checklists. Distinguish P0 quality blockers from minor source-document formatting.
10. `hoc-y`, `mcq`, `thau-hieu` remain **chat-first**, with no Python dependency. These protocols become readable instructions for such skills, and are executable only where tools exist.

## Evidence and scope

- Noise pilot: 12 MCQ from 12 different PDF pages. Accident pilot: 8 MCQ from 8 pages. These are **small pilots**, not comprehensive exams.
- Per-item metadata stores `source_anchor.source_id`, `pdf_page`, `pdf_sha256`, `exact_quote` verified against real PDF text and contextual competency.
- Browser report checks visible feedback. No independent examiner or learner-response item analysis has been performed; `semantic_validated=false` and `release_allowed=false`.
- Learner-facing lecture PDFs, when created, must omit provenance, bibliography, and meta-warning footer. Maintain internal QA separately.
