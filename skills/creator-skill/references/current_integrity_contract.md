# Beta 1.4 — Runtime data and release contract

Scope: educational skill ecosystem (26 skills). This file supersedes conflicting legacy lines about source redaction, quotas and self-approval. **It does not certify medical content.**

## Nonnegotiable user constraints

- A standalone skill can run by itself. Under `giao-trinh-tong-hop`, exactly FOUR working files must be delivered: lecture PDF, flashcard HTML, MCQ HTML, MEQ HTML.
- Lecture PDF **maximum 9 pages**, with no artificial minimum. Read complete applicable sources before selecting the priority learning concepts; 9 pages applies to the lecture OUTPUT, not source retrieval or the other three products.
- Domain-aware, multi-label objectives P0–P4. Core objectives are protected against omission. A zero-P0 set requires an independent written justification, not simply an empty array.
- Source priority for exam-aligned content: lecture Vid / instructor voice, then Slide and PNT **as defaults**, not exclusion filters. Preserve unique tables, images, distinctions and important concepts from lower-priority sources. If sources conflict, keep attribution, indicate the conflict and distinguish verified external evidence.
- Never edit the canonical source bytes merely to redact a URL, email, IP or other string. Privacy views must be separate from stored canonical data.

## Source ingestion

- `import-md` must receive a complete cartridge: index + manifest + all source Markdown files, exact bijective file mappings and valid SHA-256 digests. A partial cartridge must not replace an existing subject.
- Validate ZIP path traversal, duplicate normalized/case-folded destinations, archive count/size limits, manifest/index reconciliation and NotebookLM UUID consistency before commit.
- Write into staging and replace only references data; on commit failure, restore the previous reference snapshot. Keep a durable off-machine backup as a separate connector-mediated task; local Python import does NOT automatically upload to Google Drive.
- Every downstream consumer must verify manifest/index/source consistency, require explicit lesson resolution and fail on ambiguous or empty queries. NotebookLM UUID identifies a notebook; it does NOT guarantee that all pages were retrieved or that a source ID was resolved.

## Release gate

- Manifests must contain `lesson_id`, `generation_run_id`, `source_snapshot_sha256`, `kind` and `artifact_sha256` equal to the bytes of the actual delivered file. A reviewer note about a specific artifact must refer to its exact hash and run/snapshot.
- Self-declared reviewer names are not external identity authentication. At least the 3 cross-discipline review scopes must use distinct reviewer IDs; the release gate still requires trustworthy human evaluation for academic correctness.
- A JSON payload without working HTML controls is not a working flashcard/MCQ/MEQ. Probe explicitly identified content containers; static UI presence is only a prerequisite. Run the independent Chromium smoke script for the *exact* three HTML files and supply its JSON via `browser_evidence_path`.
- The release gate does not establish genuine student learning effectiveness. Use blind comparison and source-grounded review across multiple domains; do not substitute PASS counters for evidence.

## Required known limitations for Beta 1.4

- No live NotebookLM source retrieval was performed in this build.
- Browser smoke covers essential flip, answer and review-mode UI, not complete MEQ grading, accessibility, persistence or visual fidelity.
- The rollback mechanism protects imports performed through this Python entrypoint and import processes competing on the same lock. Concurrent *readers* of the references directory need a separate snapshot/version protocol to avoid a very short replacement window.
- The Python importer does NOT perform external Google Drive backup/upload itself, even though older instruction text may describe such a workflow.
