# Changelog

## [1.0.0] - 2026-11-21

### Added
- **Agent Plugins 1.0.0** canonical root manifest (`plugin.json`) and portable `mcp.json` (compatible with Google/Antigravity, OpenAI Codex, Cursor, Microsoft).
- **Claude Code** dual-compatibility layer (`.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `hooks/hooks.json`).
- **4 Progressive-Disclosure Skills** under `skills/`:
  - `thau-hieu` (`v6.0.0`): 4-question meta-cognitive task router + adaptive profile + lazy-loaded Medical & Learning packs.
  - `creator-skill` (`v10.0.0`): 4-Stream Sweet Spot workflow + Zero-Loss Semantic Preservation + Medical Clinical AI Consensus Pack + 15 Python scripts.
  - `ui-ux` (`v2.0.0`): W3C DTCG base & medical design tokens, WCAG 2.2 AA/AAA linter, Mayer cognitive ergonomics, NHS Clinical UX pack.
  - `qa-qc` (`v4.0.0`): Zero-User-Tester policy, 6-Layer QA Pyramid, HealthBench Medical Safety QA rubric, 28-function Python QA harness.
- **Zero-dependency Python 3.12 MCP Stdio Server** (`mcp-server/server.py`) exposing 7 tools:
  - Engineering: `qa_audit_python_file`, `ui_check_wcag_contrast`, `skill_validate_directory`, `pm_analyze_blast_radius`.
  - PHI-guarded Clinical EBM: `medical_search_pubmed`, `medical_search_clinical_trials`, `medical_search_openfda_drug`.
  - MCP Resources exposing W3C Design Tokens and Clinical QA rubrics.
- **Optional HL7 FHIR R4 Connector Template** (`mcp.fhir.example.json`) using environment variables only.
- **4 Specialized Subagent Definitions** (`agents/`), automated validator (`scripts/validate_plugin.py`), E2E stdio unit test suite (`tests/test_mcp_server.py`), and GitHub Actions CI (`.github/workflows/validate-plugin.yml`).
