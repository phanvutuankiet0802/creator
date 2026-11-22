# Product-first iteration protocol — Beta 1.18

## Why this protocol exists
Previous cycles spent many rounds auditing source images without generating a complete learner experience. That work is useful for detecting dangerous claims, but it must not block every other independent improvement indefinitely.

## Priority rule
1. Protect against material clinical harm and fabricated provenance. Preserve unreconciled high-risk source claims in private QA; avoid building exam keys from them as unconditional rules.
2. With sufficiently understood source scope, produce an **experimental** full four-artifact pack and test it in the user's intended environment. Label it not academically certified. Do not claim final academic release until verified source scope and clinical/semantic review.
3. Score **actual learner-visible outputs**: lecture flow, coverage and depth, first flashcard priorities, realistic MCQ distractors, case-data necessity, staged MEQ reasoning and browser interaction.
4. Reproduce the most impactful failure, improve the originating builder or content plan, re-build all four, then compare old/new and record actual evidence. Do not merely add a new instruction or increase a unit-test count.
5. Use adaptive quantities. Never add meaningless context or filler solely to satisfy quotas, length parity or page count.
6. Report independent dimensions: technical QA PASS, source completeness, medical risk hold, readability/depth review, clinical reasoning discrimination and learner validation. Technical PASS is not an academic certificate.
7. Time-box research without sacrificing clinical safety: route unresolved noncritical claims to a separate QA backlog; do not block an experimental prototype when the content can safely omit them. Treat unresolved critical claims as a hold on final release.
8. The completed lecture PDF must never show references, inline citations, source IDs, or QA/provenance/process commentary. Keep those in a separate internal QA document; final PDF black/white, 12pt Times New Roman or disclosed metric-compatible alternative, ≤9 A4 pages, readable flowcharts and final objective summary.

## Bug discovered in the actual Beta 1.18 trial
`tao-de` previously displayed `BỘ CÂU HỎI ÔN TẬP CHUẨN BỘ MÔN` and a university-branded header in the HTML by default, despite no verifiable department endorsement. Such authority cues must not be added by default. The provisional training title is neutral; formal affiliation requires a verified, explicitly authorized source.

## Evidence from lesson 4 trial
- Old: nine-page PDF beginning with surgical history; 62 flashcards including four historical opening cards; 44 MCQ; eight MEQ cases. These counts do not determine quality.
- New experimental build: seven-page patient-decision PDF with schematic, 38 core cards, 24 MCQ, four MEQ with 21 short clinical reasoning prompts. Browser interactions tested and new product QA nine checks passed. Comparative improvements in order/content are observable; clinical/learning outcome superiority remains unverified.
- `MEQ` builder currently requires wording such as `Nêu đúng 01` even for prompts asking for reasoning; the constraint may encourage atomic recall. This is an open pedagogy concern, not a pass proven by 11 validator gates.
