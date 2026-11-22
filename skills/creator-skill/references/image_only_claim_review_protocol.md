# Image-only medical PDF review — operational protocol

1. Intake every attached PDF; independently identify which are explicitly selected sources and which are same-lesson candidates. Do not infer lecturer authorship or journal validity from slide design.
2. Inspect contact sheets to prioritize pages, then full-resolution image before validating an exact medical statement. A thumbnail is not evidence of a readable dose or a licensed image.
3. For every high-risk claim, record source PDF, exact page, pixel digest, the **human-observed** text or diagram, the clinical question, and whether independent review is pending. Source statement and external verification are always distinct.
4. Use `scripts/visual_claim_gate.py` to detect byte/version/page mismatches and forged self-certifications; it does NOT check whether a transcription or recommendation is medically correct.
5. Beware visuals bearing generic `EBM`, `CERTIFIED`, or AI-notebook branding: these are part of the image, not validation credentials.
6. Do not pass a statement with unresolved high-risk evidence into a scored question, procedural dose instruction, or definitive decision flow. Hold the four-product release.
7. Keep citations and source provenance in internal QA, not the learner PDF. Preserve the active output contract: exactly PDF, flashcard HTML, MCQ HTML, MEQ HTML, no compulsory item count.
