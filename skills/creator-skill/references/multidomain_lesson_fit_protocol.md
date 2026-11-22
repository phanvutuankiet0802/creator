# Context-aware subject fit — operational contract (Beta 1.20)

**Purpose:** Correct the observed conflict between legacy clinical-NBME fixed quotas and the actual objectives of non-surgical lessons. Academic validity is not established by this contract or any automatic test.

## Authoring and verification order

1. Read the *actual selected source*, preserve its own argument and terminology. Declare subject, **lesson type**, audience and assessment competency for each learning objective; do not derive a universal objective list from the specialty label alone.
2. Assign which knowledge is core for this particular lesson. In a **conceptual Y học gia đình** lesson, the definition and six principles can be core: continuity, comprehensive/patient-centered care, primary contact, coordination, family and community orientation. Do not force physiological vital signs, scans or emergency management into those questions.
3. In a **time-sensitive surgical** lesson, prioritize discriminating findings, severity, timing, management tradeoffs and safety. Historical names are not implicitly P0 just because mentioned first.
4. In **environmental/occupational medicine**, scope depends on the topic: definition, exposure unit, measurement, threshold interpretation, causation, population prevention, occupational risk or legal regulation may be core. Do not hardcode either “definitions unimportant” or “always use clinical vignettes”. **A real selected source is required before claiming such a lesson has been tested.**
5. Use source-anchored items. For critical **decision items**, add a counterfactual pair that keeps options fixed while changing the finding said to drive the best answer; explain the causal pivot. A script can verify the fields and key switch, **not** the medical validity of that switch. Send to separate clinical/pedagogical review.
6. For **foundational/definition items** with genuine instructional objectives, direct conceptual questions are allowed. Balance retrieval, contrasts, error diagnosis and applied understanding without inventing pointless clinical stories.
7. Evaluate learner-visible product, including browser interactions and answer cues. Avoid an overly long correct option, fake hospital filler and an arbitrary global distribution quota. A correct answer can be long if the full set of options is natural and parallel.
8. After building, compare a surgical and a conceptual lesson in real artifacts. Describe what *changed*, not merely that domain metadata changed; record FAIL/PARTIAL when explanation quality or distractor plausibility is weak.

## Practical evidence bundle

- For `tao-de` when Python is available, `scripts/lesson_assessment_context.py::audit_lesson_items()` accepts actual full-text sources and an explicit `domain`/`lesson_type`. The adaptive HTML builder accepts optional `lesson_context` and `source_texts`; when supplied, it blocks missing source quotes and absent counterfactuals in **critical reasoning-labelled** items. The old adaptive callers remain supported, but cannot claim this QA ran without those arguments.
- `mcq` and `thau-hieu` stay **CHAT-FIRST**, with no Python requirement. They should apply the same reasoning checks linguistically and state the scope of testing.
- For conceptual YHGĐ, the real regression source is `mcq-chuyen-sau/references/sources/07_2.1_Cac_nguyen_ly_Y_hoc_gia_dinh_Vid.md`, not a made-up topic. Example output is a **6-item independent pilot**, not a complete lesson pack or validated exam.
- The surgical comparison is lesson 4 acute limb ischemia. It has genuine high-risk source conflicts and therefore remains under clinical review.
- In all cases `semantic_validated=false`, `release_allowed=false` unless a separate genuinely verified review channel approves it; a self-declared review token does not certify expertise.

## Supersession of old fixed quotas

Legacy `mcq_bloom_and_vignette_spec.md` has headings mentioning a **40-question minimum, >=85% multi-cue and >=85–90% clinical vignettes**. These values are historical and may be useful for a specifically chosen clinical exam format, but **MUST NOT be imposed as universal requirements**. The active lesson contract and user-selected source take priority. Do not read a legacy hard quota as an NBME-certified threshold.
