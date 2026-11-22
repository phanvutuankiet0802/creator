#!/usr/bin/env python3
"""Creator Agent Plugin — Zero-Dependency Python Stdio MCP Server (JSON-RPC 2.0).

Exposes 7 tools across engineering QA, UI/UX WCAG verification, Agent Skill
validation, blast-radius analysis, and PHI-guarded public clinical EBM lookup
(PubMed, ClinicalTrials.gov, OpenFDA). Uses Python standard library only.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import pathlib
import re
import sys
import traceback
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

SERVER_NAME = "creator-tools"
SERVER_VERSION = "1.0.0"
DEFAULT_PROTOCOL_VERSION = "2024-11-05"
SUPPORTED_PROTOCOLS = {"2024-11-05", "2025-03-26", "2025-06-18"}

PLUGIN_ROOT = pathlib.Path(
    os.environ.get("CREATOR_PLUGIN_ROOT") or pathlib.Path(__file__).resolve().parent.parent
).resolve()

CLINICAL_DISCLAIMER = (
    "Reference evidence only (Clinician-in-the-Loop). Verify against full peer-reviewed "
    "sources and local clinical guidelines before making diagnostic or therapeutic decisions."
)

# Patterns that strongly indicate accidental patient PHI/PII in a public search query.
PHI_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("email_address", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("ssn_like", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("phone_like", re.compile(r"\b(?:\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b")),
    ("dob_mrn_label", re.compile(r"\b(?:MRN|DOB|patient\s*id|ma\s*benh\s*nhan|so\s*cmnd|cccd)\s*[:=#-]?\s*[A-Za-z0-9/-]{4,}", re.I)),
]

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("openai_or_api_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("github_pat", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private_key_pem", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]


def _load_bundled_module(rel_path: str, module_name: str) -> Any:
    """Dynamically load a bundled skill script without polluting sys.path."""
    target = PLUGIN_ROOT / rel_path
    if not target.is_file():
        raise FileNotFoundError(f"Bundled script not found: {target}")
    spec = importlib.util.spec_from_file_location(module_name, str(target))
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to create spec for {target}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_phi_guard(text: str) -> list[str]:
    """Return list of matched PHI/PII indicator types; non-empty blocks external calls."""
    hits: list[str] = []
    for label, pattern in PHI_PATTERNS:
        if pattern.search(text or ""):
            hits.append(label)
    return hits


def _http_get_json(url: str, timeout: int = 12) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"{SERVER_NAME}/{SERVER_VERSION} (Agent-Plugins-1.0; +https://agent-plugins.org)",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


# ---------------------------------------------------------------------------
# Tool Implementations
# ---------------------------------------------------------------------------

def tool_qa_audit_python_file(args: dict[str, Any]) -> dict[str, Any]:
    file_path = pathlib.Path(str(args.get("file_path", ""))).expanduser()
    if not file_path.is_file():
        return {"verdict": "NO-GO", "error": f"File not found: {file_path}"}
    code = file_path.read_text(encoding="utf-8", errors="replace")

    qa_mod = _load_bundled_module("skills/qa-qc/scripts/qa_test_harness.py", "creator_qa_harness")
    ast_report = qa_mod.run_ast_and_static_security_scan(code, str(file_path))

    secret_hits = [label for label, pat in SECRET_PATTERNS if pat.search(code)]
    phi_hits = check_phi_guard(code)

    passed = True
    if isinstance(ast_report, dict):
        if ast_report.get("passed") is False or ast_report.get("status") == "FAIL":
            passed = False
        if ast_report.get("errors") or ast_report.get("critical_issues"):
            passed = False
    if secret_hits:
        passed = False

    return {
        "file": str(file_path),
        "verdict": "GO" if passed else "NO-GO",
        "secret_leaks": secret_hits,
        "phi_warnings": phi_hits,
        "ast_security_report": ast_report,
    }


def tool_ui_check_wcag_contrast(args: dict[str, Any]) -> dict[str, Any]:
    fg = str(args.get("foreground_hex", "")).strip()
    bg = str(args.get("background_hex", "")).strip()
    hex_re = re.compile(r"^#?[0-9A-Fa-f]{6}$")
    if not hex_re.match(fg) or not hex_re.match(bg):
        return {"error": "foreground_hex and background_hex must be 6-digit hex colors (e.g. #0F172A, #FFFFFF)."}
    if not fg.startswith("#"):
        fg = "#" + fg
    if not bg.startswith("#"):
        bg = "#" + bg

    ui_mod = _load_bundled_module("skills/ui-ux/scripts/ui_ergonomics_linter.py", "creator_ui_linter")
    ratio = float(ui_mod.compute_wcag_contrast_ratio(fg, bg))
    return {
        "foreground": fg.upper(),
        "background": bg.upper(),
        "contrast_ratio": round(ratio, 2),
        "wcag_2_2": {
            "ui_components_and_large_text_aa_3_0": ratio >= 3.0,
            "normal_text_aa_4_5": ratio >= 4.5,
            "normal_text_aaa_7_0": ratio >= 7.0,
            "clinical_high_contrast_recommended": ratio >= 7.0,
        },
    }


def tool_skill_validate_directory(args: dict[str, Any]) -> dict[str, Any]:
    skill_dir = pathlib.Path(str(args.get("skill_dir", ""))).expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []

    if not skill_dir.is_dir():
        return {"verdict": "NO-GO", "errors": [f"Directory not found: {skill_dir}"]}

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return {"verdict": "NO-GO", "errors": [f"Missing required SKILL.md in {skill_dir}"]}

    content = skill_md.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\n(.*?)\n---\n", content, re.S)
    name_val = ""
    desc_val = ""
    if not m:
        errors.append("Missing YAML frontmatter block delimited by ---")
    else:
        fm = m.group(1)
        nm = re.search(r"^name:\s*(.+)$", fm, re.M)
        dm = re.search(r"^description:\s*['\"]?(.+?)['\"]?$", fm, re.M)
        name_val = nm.group(1).strip().strip("'\"") if nm else ""
        desc_val = dm.group(1).strip() if dm else ""
        if name_val != skill_dir.name:
            errors.append(f"Frontmatter name '{name_val}' must match directory name '{skill_dir.name}'")
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name_val) or len(name_val) > 64:
            errors.append(f"Invalid kebab-case skill name: '{name_val}'")
        if not desc_val or len(desc_val) > 1024:
            errors.append(f"Description length ({len(desc_val)}) must be within 1..1024 characters")

    line_count = len(content.splitlines())
    est_tokens = len(content) // 4
    if line_count >= 500:
        errors.append(f"SKILL.md has {line_count} lines (agentskills.io spec recommends < 500 lines)")
    elif line_count > 300:
        warnings.append(f"SKILL.md has {line_count} lines; consider moving details into references/")
    if est_tokens >= 5000:
        warnings.append(f"SKILL.md estimated tokens (~{est_tokens}) exceeds 5,000-token target")

    refs = sorted(set(re.findall(r"`((?:references|scripts|tokens|assets|evals|examples)/[A-Za-z0-9_./-]+)`", content)))
    for ref in refs:
        if ref.count("/") != 1:
            errors.append(f"Reference exceeds 1-level depth: {ref}")
        if not (skill_dir / ref).is_file():
            errors.append(f"Broken relative reference in SKILL.md: {ref}")

    py_checked = 0
    json_checked = 0
    for fp in sorted(skill_dir.rglob("*")):
        if not fp.is_file():
            continue
        if fp.suffix == ".py":
            py_checked += 1
            try:
                ast.parse(fp.read_text(encoding="utf-8"), filename=str(fp))
            except SyntaxError as exc:
                errors.append(f"Python syntax error in {fp.relative_to(skill_dir)}: {exc}")
        elif fp.suffix == ".json":
            json_checked += 1
            try:
                json.loads(fp.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"Invalid JSON in {fp.relative_to(skill_dir)}: {exc}")

    return {
        "skill": skill_dir.name,
        "verdict": "GO" if not errors else "NO-GO",
        "metrics": {
            "skill_md_lines": line_count,
            "estimated_tokens": est_tokens,
            "description_chars": len(desc_val),
            "references_verified": len(refs),
            "python_scripts_checked": py_checked,
            "json_files_checked": json_checked,
        },
        "errors": errors,
        "warnings": warnings,
    }


def tool_pm_analyze_blast_radius(args: dict[str, Any]) -> dict[str, Any]:
    root_dir = pathlib.Path(str(args.get("root_dir", str(PLUGIN_ROOT)))).expanduser().resolve()
    target_symbol = str(args.get("target_symbol", "")).strip()
    if not root_dir.is_dir():
        return {"error": f"Directory not found: {root_dir}"}

    ignore_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"}
    files_by_ext: dict[str, int] = {}
    py_symbols: dict[str, list[str]] = {}
    symbol_matches: list[dict[str, Any]] = []

    for fp in sorted(root_dir.rglob("*")):
        if not fp.is_file() or any(part in ignore_dirs for part in fp.parts):
            continue
        ext = fp.suffix.lower() or "<no-ext>"
        files_by_ext[ext] = files_by_ext.get(ext, 0) + 1
        rel = str(fp.relative_to(root_dir))

        if fp.suffix == ".py":
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(text, filename=rel)
                defs = [
                    n.name
                    for n in tree.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                ]
                py_symbols[rel] = defs
            except SyntaxError:
                py_symbols[rel] = ["<syntax-error>"]

        if target_symbol and fp.suffix.lower() in {".py", ".md", ".json", ".yaml", ".yml", ".ts", ".tsx", ".js"}:
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
                count = text.count(target_symbol)
                if count > 0:
                    symbol_matches.append({"file": rel, "occurrences": count})
            except OSError:
                pass

    return {
        "root_dir": str(root_dir),
        "total_files": sum(files_by_ext.values()),
        "files_by_extension": dict(sorted(files_by_ext.items())),
        "python_modules_count": len(py_symbols),
        "total_top_level_python_defs": sum(len(v) for v in py_symbols.values()),
        "target_symbol": target_symbol or None,
        "impacted_files": symbol_matches,
    }


def tool_medical_search_pubmed(args: dict[str, Any]) -> dict[str, Any]:
    query = str(args.get("query", "")).strip()
    max_results = max(1, min(int(args.get("max_results", 5)), 20))
    if not query:
        return {"error": "query is required"}

    phi_hits = check_phi_guard(query)
    if phi_hits:
        return {
            "blocked": True,
            "reason": "PHI/PII Guard blocked outbound query to public PubMed API.",
            "detected_patterns": phi_hits,
        }

    try:
        esearch_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
            + urllib.parse.urlencode({"db": "pubmed", "term": query, "retmode": "json", "retmax": max_results, "sort": "relevance"})
        )
        search_data = _http_get_json(esearch_url)
        pmids = search_data.get("esearchresult", {}).get("idlist", [])
        if not pmids:
            return {"query": query, "count": 0, "articles": [], "disclaimer": CLINICAL_DISCLAIMER}

        esummary_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?"
            + urllib.parse.urlencode({"db": "pubmed", "id": ",".join(pmids), "retmode": "json"})
        )
        summary_data = _http_get_json(esummary_url).get("result", {})
        articles = []
        for pmid in pmids:
            item = summary_data.get(pmid, {})
            articles.append(
                {
                    "pmid": pmid,
                    "title": item.get("title", ""),
                    "journal": item.get("fulljournalname") or item.get("source", ""),
                    "pubdate": item.get("pubdate", ""),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                }
            )
        return {"query": query, "count": len(articles), "articles": articles, "disclaimer": CLINICAL_DISCLAIMER}
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return {
            "query": query,
            "network_error": str(exc),
            "note": "PubMed requires outbound HTTPS access to eutils.ncbi.nlm.nih.gov.",
            "disclaimer": CLINICAL_DISCLAIMER,
        }


def tool_medical_search_clinical_trials(args: dict[str, Any]) -> dict[str, Any]:
    condition = str(args.get("condition", "")).strip()
    intervention = str(args.get("intervention", "")).strip()
    max_results = max(1, min(int(args.get("max_results", 5)), 20))
    if not condition and not intervention:
        return {"error": "At least one of 'condition' or 'intervention' is required"}

    phi_hits = check_phi_guard(f"{condition} {intervention}")
    if phi_hits:
        return {
            "blocked": True,
            "reason": "PHI/PII Guard blocked outbound query to public ClinicalTrials.gov API.",
            "detected_patterns": phi_hits,
        }

    params: dict[str, Any] = {"pageSize": max_results, "format": "json"}
    if condition:
        params["query.cond"] = condition
    if intervention:
        params["query.intr"] = intervention

    try:
        url = "https://clinicaltrials.gov/api/v2/studies?" + urllib.parse.urlencode(params)
        data = _http_get_json(url)
        studies = []
        for st in data.get("studies", []):
            proto = st.get("protocolSection", {})
            ident = proto.get("identificationModule", {})
            status_mod = proto.get("statusModule", {})
            design_mod = proto.get("designModule", {})
            cond_mod = proto.get("conditionsModule", {})
            nct_id = ident.get("nctId", "")
            studies.append(
                {
                    "nct_id": nct_id,
                    "title": ident.get("briefTitle", ""),
                    "status": status_mod.get("overallStatus", ""),
                    "phases": design_mod.get("phases", []),
                    "conditions": cond_mod.get("conditions", []),
                    "url": f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "",
                }
            )
        return {"count": len(studies), "studies": studies, "disclaimer": CLINICAL_DISCLAIMER}
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return {
            "network_error": str(exc),
            "note": "ClinicalTrials.gov requires outbound HTTPS access to clinicaltrials.gov.",
            "disclaimer": CLINICAL_DISCLAIMER,
        }


def tool_medical_search_openfda_drug(args: dict[str, Any]) -> dict[str, Any]:
    drug_name = str(args.get("drug_name", "")).strip()
    max_results = max(1, min(int(args.get("max_results", 3)), 10))
    if not drug_name:
        return {"error": "drug_name is required"}

    phi_hits = check_phi_guard(drug_name)
    if phi_hits:
        return {
            "blocked": True,
            "reason": "PHI/PII Guard blocked outbound query to public OpenFDA API.",
            "detected_patterns": phi_hits,
        }

    safe_term = re.sub(r'["\\]', "", drug_name)
    search_expr = f'openfda.generic_name:"{safe_term}"+openfda.brand_name:"{safe_term}"'
    url = f"https://api.fda.gov/drug/label.json?search={urllib.parse.quote(search_expr, safe=':+:\"')}&limit={max_results}"

    def _snippet(items: list[str] | None, limit: int = 500) -> str:
        if not items:
            return ""
        joined = " ".join(items).strip()
        return joined[:limit] + ("..." if len(joined) > limit else "")

    try:
        data = _http_get_json(url)
        labels = []
        for r in data.get("results", []):
            ofda = r.get("openfda", {})
            labels.append(
                {
                    "brand_names": ofda.get("brand_name", [])[:3],
                    "generic_names": ofda.get("generic_name", [])[:3],
                    "boxed_warning": _snippet(r.get("boxed_warning")),
                    "indications_and_usage": _snippet(r.get("indications_and_usage")),
                    "contraindications": _snippet(r.get("contraindications")),
                    "dosage_and_administration": _snippet(r.get("dosage_and_administration")),
                }
            )
        return {"drug_name": drug_name, "count": len(labels), "labels": labels, "disclaimer": CLINICAL_DISCLAIMER}
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return {
            "drug_name": drug_name,
            "network_error": str(exc),
            "note": "OpenFDA requires outbound HTTPS access to api.fda.gov.",
            "disclaimer": CLINICAL_DISCLAIMER,
        }


TOOLS_REGISTRY: list[dict[str, Any]] = [
    {
        "name": "qa_audit_python_file",
        "description": "Run AST, static security, secret-leak, and PHI-hygiene audit on a Python file using the bundled qa-qc harness.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the Python file to audit."}
            },
            "required": ["file_path"],
        },
        "handler": tool_qa_audit_python_file,
    },
    {
        "name": "ui_check_wcag_contrast",
        "description": "Compute exact W3C WCAG 2.2 optical contrast ratio and AA/AAA pass/fail verdict between two 6-digit hex colors.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "foreground_hex": {"type": "string", "description": "Foreground color hex (e.g. #0F172A)."},
                "background_hex": {"type": "string", "description": "Background color hex (e.g. #FFFFFF)."},
            },
            "required": ["foreground_hex", "background_hex"],
        },
        "handler": tool_ui_check_wcag_contrast,
    },
    {
        "name": "skill_validate_directory",
        "description": "Validate an Agent Skill directory against agentskills.io specification (frontmatter, <500 lines, 1-level refs, Python AST, JSON).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "skill_dir": {"type": "string", "description": "Path to the Agent Skill directory containing SKILL.md."}
            },
            "required": ["skill_dir"],
        },
        "handler": tool_skill_validate_directory,
    },
    {
        "name": "pm_analyze_blast_radius",
        "description": "Analyze project or plugin blast radius: file inventory, top-level Python AST definitions, and cross-file symbol references.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "root_dir": {"type": "string", "description": "Directory to scan (defaults to plugin root)."},
                "target_symbol": {"type": "string", "description": "Optional symbol or string to trace across files."},
            },
        },
        "handler": tool_pm_analyze_blast_radius,
    },
    {
        "name": "medical_search_pubmed",
        "description": "PHI-guarded NCBI PubMed E-utilities search returning peer-reviewed PMIDs, journals, publication dates, and URLs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "De-identified clinical/biomedical search query (no patient PHI)."},
                "max_results": {"type": "integer", "description": "Max articles to return (1-20, default 5)."},
            },
            "required": ["query"],
        },
        "handler": tool_medical_search_pubmed,
    },
    {
        "name": "medical_search_clinical_trials",
        "description": "PHI-guarded ClinicalTrials.gov v2 API search returning NCT IDs, study status, phases, conditions, and links.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "condition": {"type": "string", "description": "Disease or condition (e.g. atrial fibrillation)."},
                "intervention": {"type": "string", "description": "Drug or intervention (optional)."},
                "max_results": {"type": "integer", "description": "Max studies to return (1-20, default 5)."},
            },
        },
        "handler": tool_medical_search_clinical_trials,
    },
    {
        "name": "medical_search_openfda_drug",
        "description": "PHI-guarded OpenFDA drug label search returning boxed warnings, indications, contraindications, and dosage summaries.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "drug_name": {"type": "string", "description": "Generic or brand drug name (e.g. metformin, apixaban)."},
                "max_results": {"type": "integer", "description": "Max labels to return (1-10, default 3)."},
            },
            "required": ["drug_name"],
        },
        "handler": tool_medical_search_openfda_drug,
    },
]

TOOL_MAP = {t["name"]: t for t in TOOLS_REGISTRY}

RESOURCES_REGISTRY: list[dict[str, str]] = [
    {
        "uri": "creator://tokens/base-design-tokens",
        "name": "Universal W3C DTCG Design Tokens",
        "mimeType": "application/json",
        "rel_path": "skills/ui-ux/tokens/base_design_tokens.json",
    },
    {
        "uri": "creator://tokens/medical-design-tokens",
        "name": "Clinical Medical W3C DTCG Design Tokens",
        "mimeType": "application/json",
        "rel_path": "skills/ui-ux/tokens/medical_design_tokens.json",
    },
    {
        "uri": "creator://medical/healthbench-qa-rubric",
        "name": "Medical Safety QA Rubric (HealthBench + G-AMIE)",
        "mimeType": "text/markdown",
        "rel_path": "skills/qa-qc/references/medical_safety_qa_rubric.md",
    },
    {
        "uri": "creator://medical/clinical-ai-consensus",
        "name": "Medical Clinical AI Consensus Pack",
        "mimeType": "text/markdown",
        "rel_path": "skills/creator-skill/references/medical_clinical_ai_consensus_pack.md",
    },
]


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 MCP Stdio Protocol Loop
# ---------------------------------------------------------------------------

def _make_response(req_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _make_error(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def handle_request(req: dict[str, Any]) -> dict[str, Any] | None:
    method = req.get("method", "")
    req_id = req.get("id")
    params = req.get("params") or {}

    # Notifications have no id and require no response.
    if method.startswith("notifications/"):
        return None

    if method == "initialize":
        client_ver = str(params.get("protocolVersion", DEFAULT_PROTOCOL_VERSION))
        negotiated = client_ver if client_ver in SUPPORTED_PROTOCOLS else DEFAULT_PROTOCOL_VERSION
        return _make_response(
            req_id,
            {
                "protocolVersion": negotiated,
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"listChanged": False},
                },
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        )

    if method == "ping":
        return _make_response(req_id, {})

    if method == "tools/list":
        public_tools = [
            {"name": t["name"], "description": t["description"], "inputSchema": t["inputSchema"]}
            for t in TOOLS_REGISTRY
        ]
        return _make_response(req_id, {"tools": public_tools})

    if method == "tools/call":
        tool_name = str(params.get("name", ""))
        tool_args = params.get("arguments") or {}
        if tool_name not in TOOL_MAP:
            return _make_error(req_id, -32602, f"Unknown tool: {tool_name}")
        try:
            output = TOOL_MAP[tool_name]["handler"](tool_args)
            is_err = bool(isinstance(output, dict) and ("error" in output or output.get("blocked")))
            return _make_response(
                req_id,
                {
                    "content": [{"type": "text", "text": json.dumps(output, ensure_ascii=False, indent=2)}],
                    "isError": is_err,
                },
            )
        except Exception as exc:
            return _make_response(
                req_id,
                {
                    "content": [{"type": "text", "text": json.dumps({"error": str(exc), "trace": traceback.format_exc(limit=3)}, ensure_ascii=False)}],
                    "isError": True,
                },
            )

    if method == "resources/list":
        public_res = [
            {"uri": r["uri"], "name": r["name"], "mimeType": r["mimeType"]}
            for r in RESOURCES_REGISTRY
        ]
        return _make_response(req_id, {"resources": public_res})

    if method == "resources/read":
        uri = str(params.get("uri", ""))
        match = next((r for r in RESOURCES_REGISTRY if r["uri"] == uri), None)
        if not match:
            return _make_error(req_id, -32602, f"Unknown resource URI: {uri}")
        fp = PLUGIN_ROOT / match["rel_path"]
        if not fp.is_file():
            return _make_error(req_id, -32603, f"Resource file missing on disk: {match['rel_path']}")
        return _make_response(
            req_id,
            {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": match["mimeType"],
                        "text": fp.read_text(encoding="utf-8"),
                    }
                ]
            },
        )

    return _make_error(req_id, -32601, f"Method not found: {method}")


def main() -> int:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as exc:
            sys.stdout.write(json.dumps(_make_error(None, -32700, f"Parse error: {exc}")) + "\n")
            sys.stdout.flush()
            continue

        resp = handle_request(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
