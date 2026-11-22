# Source-bound objective review gate (Beta 1.15)

1. Full selected source text must be loaded and hashed. Student presentation may remain a taught-session record but the student-authored objectives are *candidates*, not an approved syllabus.
2. Before authoring, propose P0/P1/P3 by **subject, type of problem, threat to patient safety, causal importance and real assessment goal**. Do not rank by source ordering, mention frequency or a quota; history may be brief despite being the first objective in a source.
3. Each candidate must include exact unchanged `source_quote`, `source_line`, selected `source_id`, intended four-product role, and reason. A citation/hash proves traceability, not truth.
4. `scripts/lesson_objective_gate.py` checks source bytes, quoted line and a four-product plan. Its only possible successful technical result is `HOLD_FOR_ACADEMIC_REVIEW`. It does **not** certify 90% coverage, author qualifications or medical accuracy.
5. Resolve safety-critical contradictions using independent full guideline evidence and *case-specific* context. Do not convert warnings into single-answer MCQs until expert review clears them.
6. For MCQ with long cases, use a clinical-context-ablation trial: ask whether the exact answer remains obtainable after removing patient findings. If yes, downgrade the case to concise knowledge assessment or revise the question to genuinely require clinical facts. Apply specialist judgment rather than a fixed quota.
7. For PDF lectures, preserve black/white, 12pt main teaching content, <=9 A4 pages, diagrams and end-of-lesson LO summary, with no visible sources/citations/references; provenance resides in QA sidecars outside the exact four delivered learner files.
8. Source slides may include figures/ECG and image-only material. Extracting all Markdown does NOT constitute visually checking all figures. Document the visual audit separately before claiming full source coverage.
9. Standalone skills follow the same reasoning even without `creator-skill` installed. `hoc-y`, `mcq`, `thau-hieu` remain chat-first, no Python dependency.

## Example (lesson 4 ALI)
An unusual student-presented classroom session puts surgical-history objectives first. Do not turn that ordering into flashcard or PDF priority. The clinically urgent decision skills (limb viability, Rutherford class, urgency, initial management, reperfusion complications) are proposed higher-priority, **pending expert confirmation**. Refer to the internal lesson 4 review board in the checkpoint bundle; no learner-facing citations.
