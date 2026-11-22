# Active Authoring & Adversarial Review Protocol v1.2

This file is normative for academic generation. Legacy LOCK/FB clauses are historical and MUST NOT override this file, the 9-page ceiling, the 4-file orchestrator contract, or the user's declared objective.

## 1. First, understand the requested lesson
1. Read the FULL user-selected source via @nap-data Markdown (Vid/Slide/PNT), NotebookLM by UUID through a **real connected tool** (not UUID text as evidence), or attached documents. Report missing/unreadable source fragments and never simulate a connector response. Keep original wording for factual verification.
2. Classify **each objective**, not just the course: domain labels, competency, importance P0/P1/P2/P3/P4, source locations, rationale and what failure means. These are proposals for a distinct academic reviewer, not verified ground truth. A mixed topic can have mixed labels.
3. Separate `SOURCE_TAUGHT` and `EXTERNALLY_VERIFIED` knowledge. Never silently rewrite a disputed source claim. Preserve the source statement, add a clearly marked note explaining the verified update and its citation when verification is possible; otherwise mark `NEEDS_VERIFICATION` without inventing supporting evidence.
4. Select the appropriate assessment for each objective; do not force a clinical decision, identical difficulty ratios, or arbitrary per-lesson quantities on different subjects.

## 2. Lecture: teach, do not compress a keyword inventory
A. Summarize what the learner must ultimately be able to DO. Build an explanation graph: prerequisite -> central mechanism/decision rule -> observable consequence -> worked example -> synthesis. Each new concept must answer 'why this follows' as needed; show distinctions/limitations.
B. Reserve most of the available 9 pages for P0/P1 reasoning. P2 supports comprehension. P3/P4 appear only when the lesson demands them. **A long source is NOT a command to enumerate every Vid proposition.** History and epidemiology may be P0 in history/public-health lessons and peripheral in procedural lessons; justify rather than use a global ban.
C. At most **9 A4 pages** including diagrams. Do not shrink font or fill pages with semicolon fragments to meet source recall. If all P0/P1 cannot fit clearly, return `SCOPE_CONFLICT` with the specific conflicting objectives, not a fraudulent 'passed' PDF. Do not silently create a tenth page or a second PDF when orchestrated.
D. After drafting, simulate a novice reading sections in order: check assumed prerequisites, ambiguous referents, abrupt causal jumps, unmotivated tables, duplicate facts and misleading absolute statements. Rephrase before rendering. In a 9-page lecture, assess comprehension, NOT word count or copied-word recall.

## 3. Flashcards: coverage rather than counting
Generate a concept ledger covering each P0/P1 fact, mechanism, contrast and common confusion appropriate for retrieval. Give each card ONE clear retrieval task, a concise answer with necessary causal explanation and a meaningful discriminating cue. Exclude trivial dates, historical firsts, percentages and unsupported mnemonics unless the objective/likely examination genuinely requires them. Independently scan for missing critical concepts and near-duplicate fronts. Counts are flexible; P0 coverage is not.

## 4. MCQ: item-writing and true discrimination
Every reasoning item must pass the **case-dependence ablation**: hide the vignette's specific patient/data; if the correct answer remains readily obtainable from the last line or a memorized definition, reclassify as recall or REWRITE the scenario/question. A long stem, Bloom label, metadata 'decision point' or balanced A/B/C/D distribution is never evidence of complexity. Demand plausible distractors representing genuine competing interpretations and explanation for each, including decisive clues and why alternatives fail. For case-based P0 questions, add two linked evidence steps in the *answer explanation*, not fabricated reasoning metadata. Distractors must not be absurd or artificially extended for length parity. Check answer exposure across neighboring items and visuals. Never claim psychometric discrimination without student response data.

## 5. MEQ: unfolding, domain-appropriate assessment
Design stage 1 as genuinely incomplete information; each next stage supplies a NEW meaningful observation/test/treatment response that changes or refines at least one reasoning step. Preserve staged disclosure in UI. Titles and stage labels must be diagnosis-neutral when the task asks the student to derive that diagnosis, classification or intervention. Do not leak correct terms in placeholder text or visuals. Mix evidence identification, explanation, differential, interpretation, calculation, prioritization, management choice or critical appraisal according to the domain; NOT every question must request treatment. A case needs a scored, explicit reasoning path: correct conclusion, supporting findings, rival explanations where the question demands comparison, and a response to new information. Do not confuse 'two keyword hits' with valid clinical reasoning; keyword autograding is optional formative feedback and must be labelled as such.

## 6. Distinct independent review with adversarial evidence
Separate roles: author/producer builds artifacts; @tham-dinh-su-pham reviews learning objectives, explanatory chains, MCQ ablations and MEQ stage progression; @qa-qc tests rendering, JS interactions and output contracts; @creator-skill coordinates and refuses unsupported release claims. Reviewers must inspect real artifact/source, not merely pass their own mock data or attach a metadata flag. A report records item IDs, source anchors, observed defect, attempted counterexample and required rewrite. The structural engine is only a first gate; independent semantic review and user-facing testing remain required.

## 7. Delivery invariants
- `giao-trinh-tong-hop`: EXACTLY 4 files (lecture PDF, flashcard HTML, MCQ HTML, MEQ HTML) even when some categories get fewer items, never fewer file types. A clear, usable minimal MEQ is preferred to filler, but all 4 must exist.
- Lecture PDF <= 9 pages, consistent readability. Every original bundle skill works independently when invoked alone and can be orchestrated with explicit dependency and trace.
- Do not run legacy hard quotas as a second mandatory gate in the adaptive path. Preserve legacy features (interactive HTML, images, downloadable data) while checking their behavior.

## 8. Domain-based exemplars (not rigid global prescriptions)
- Surgery: recognize time-sensitive danger, severity, alternatives, timing and consequences; historical names usually not central.
- Physiology: mechanisms, feedback, prediction after parameter changes; clinical choices optional.
- Anatomy: spatial relations, structures, injury effects; use image when spatial knowledge is essential.
- Pharmacology: mechanism, indications, interactions, dose reasoning if sources support it, patient-specific differentiation.
- Public health / epidemiology: denominators, bias, confounding, study design and interpretation; epidemiology may be CENTRAL.
- Imaging: image findings and differential, modality tradeoffs; do not invent image-only findings without source image.
- Oncology: evolving pathology and stage, tests, treatment constraints and follow-up; cover intermediate justifications, not just final diagnosis.

## 9. Self-adversarial loop before publishing
For each product, submit 3+ hard objections and revise: (1) which critical objective is missing? (2) where does a novice lose the thread? (3) can questions be answered without evidence or are options cueing? Include at least one cross-topic test (e.g. physiology/public-health) in addition to surgical examples. Label results as `REVIEW_REQUIRED` until the real artifacts are reviewed. Do not self-issue evidence of independent review.
