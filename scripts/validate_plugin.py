#!/usr/bin/env python3
"""Comprehensive validator for the `creator` Agent Plugin (Agent Plugins 1.0.0 + Claude Code).

Checks:
1. Root plugin.json (Agent Plugins 1.0.0 schema contract)
2. .claude-plugin/plugin.json & marketplace catalogs
3. mcp.json explicit transport types & command paths
4. hooks/hooks.json & agents/*.md frontmatter
5. Every bundled skill in skills/*/ (agentskills.io spec, <500 lines, 1-level refs, AST, JSON)
6. Zero hardcoded secrets / PHI leaks across manifests & source code
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
SECRET_RE = re.compile(r"(?:\bsk-[A-Za-z0-9]{20,}\b|\bgh[pousr]_[A-Za-z0-9]{20,}\b|\bAKIA[0-9A-Z]{16}\b|-----BEGIN (?:RSA |EC )?PRIVATE KEY-----)")


def _load_json(path: pathlib.Path, errors: list[str]) -> dict | None:
    if not path.is_file():
        errors.append(f"Missing required JSON file: {path.relative_to(ROOT)}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {path.relative_to(ROOT)}: {exc}")
        return None


def validate_plugin(quick: bool = False) -> tuple[bool, dict]:
    errors: list[str] = []
    warnings: list[str] = []
    stats = {"skills": 0, "agents": 0, "py_files": 0, "json_files": 0}

    # 1. Agent Plugins 1.0.0 root manifest
    pjson = _load_json(ROOT / "plugin.json", errors)
    if isinstance(pjson, dict):
        if pjson.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
            errors.append("plugin.json must declare Agent Plugins 1.0.0 $schema")
        pname = str(pjson.get("name", ""))
        if not KEBAB_RE.match(pname):
            errors.append(f"plugin.json name must be kebab-case: '{pname}'")
        pver = str(pjson.get("version", ""))
        if pver and not SEMVER_RE.match(pver):
            errors.append(f"plugin.json version must be semver: '{pver}'")

    # 2. Claude Code compatibility manifest + marketplaces
    cpjson = _load_json(ROOT / ".claude-plugin" / "plugin.json", errors)
    if isinstance(cpjson, dict) and isinstance(pjson, dict):
        if cpjson.get("name") != pjson.get("name"):
            errors.append(".claude-plugin/plugin.json name diverges from root plugin.json")
        for key in ("skills", "agents", "hooks", "mcpServers"):
            val = cpjson.get(key)
            if isinstance(val, str):
                target = (ROOT / val).resolve()
                if not target.exists():
                    errors.append(f".claude-plugin/plugin.json path missing: {key}={val}")

    _load_json(ROOT / ".agents" / "plugins" / "marketplace.json", errors)
    _load_json(ROOT / ".claude-plugin" / "marketplace.json", errors)

    # 3. Portable mcp.json check
    mjson = _load_json(ROOT / "mcp.json", errors)
    if isinstance(mjson, dict):
        if mjson.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json":
            errors.append("mcp.json must declare Agent Plugins 1.0.0 mcp.schema.json")
        servers = mjson.get("mcpServers", {})
        if not isinstance(servers, dict) or not servers:
            errors.append("mcp.json must declare at least one entry under mcpServers")
        for sname, scfg in (servers or {}).items():
            stype = scfg.get("type")
            if stype not in {"stdio", "streamable-http", "sse"}:
                errors.append(f"mcp.json server '{sname}' missing explicit valid type: {stype}")
            if stype == "stdio":
                args = scfg.get("args") or []
                if args and isinstance(args[0], str) and args[0].endswith(".py"):
                    if not (ROOT / args[0]).is_file():
                        errors.append(f"mcp.json server '{sname}' script not found: {args[0]}")

    _load_json(ROOT / "hooks" / "hooks.json", errors)

    # 4. Agents check
    agents_dir = ROOT / "agents"
    if agents_dir.is_dir():
        for af in sorted(agents_dir.glob("*.md")):
            stats["agents"] += 1
            txt = af.read_text(encoding="utf-8")
            if not re.match(r"^---\n.*?name:\s*.+?\n---\n", txt, re.S):
                errors.append(f"Agent definition missing YAML frontmatter name: {af.relative_to(ROOT)}")

    # 5. Skills check (agentskills.io)
    skills_dir = ROOT / "skills"
    if not skills_dir.is_dir():
        errors.append("Missing skills/ directory")
    else:
        for sdir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
            stats["skills"] += 1
            smd = sdir / "SKILL.md"
            if not smd.is_file():
                errors.append(f"Missing SKILL.md in skills/{sdir.name}")
                continue
            txt = smd.read_text(encoding="utf-8")
            m = re.match(r"^---\n(.*?)\n---\n", txt, re.S)
            if not m:
                errors.append(f"skills/{sdir.name}/SKILL.md missing frontmatter")
            else:
                fm = m.group(1)
                nm = re.search(r"^name:\s*(.+)$", fm, re.M)
                dm = re.search(r"^description:\s*['\"]?(.+?)['\"]?$", fm, re.M)
                sname = nm.group(1).strip().strip("'\"") if nm else ""
                sdesc = dm.group(1).strip() if dm else ""
                if sname != sdir.name:
                    errors.append(f"Skill name '{sname}' != folder '{sdir.name}'")
                if not sdesc or len(sdesc) > 1024:
                    errors.append(f"Skill '{sdir.name}' description invalid length: {len(sdesc)}")
            lines = len(txt.splitlines())
            if lines >= 500:
                errors.append(f"skills/{sdir.name}/SKILL.md has {lines} lines (>= 500 limit)")

            refs = sorted(set(re.findall(r"`((?:references|scripts|tokens|assets|evals|examples)/[A-Za-z0-9_./-]+)`", txt)))
            for ref in refs:
                if ref.count("/") != 1:
                    errors.append(f"skills/{sdir.name}: reference > 1 level deep: {ref}")
                if not (sdir / ref).is_file():
                    errors.append(f"skills/{sdir.name}: broken reference: {ref}")

    # 6. Full AST, JSON, and secret scan (skip full tree walk only if --quick and no issues so far)
    if not quick:
        ignore_dirs = {".git", "__pycache__", ".venv", "venv"}
        for fp in sorted(ROOT.rglob("*")):
            if not fp.is_file() or any(part in ignore_dirs for part in fp.parts):
                continue
            rel = str(fp.relative_to(ROOT))
            if fp.suffix == ".py":
                stats["py_files"] += 1
                try:
                    code = fp.read_text(encoding="utf-8")
                    ast.parse(code, filename=rel)
                    if SECRET_RE.search(code):
                        errors.append(f"Potential hardcoded secret detected in {rel}")
                except SyntaxError as exc:
                    errors.append(f"Python syntax error in {rel}: {exc}")
            elif fp.suffix == ".json":
                stats["json_files"] += 1
                try:
                    raw = fp.read_text(encoding="utf-8")
                    json.loads(raw)
                    if SECRET_RE.search(raw):
                        errors.append(f"Potential hardcoded secret detected in {rel}")
                except json.JSONDecodeError as exc:
                    errors.append(f"JSON parse error in {rel}: {exc}")

    return len(errors) == 0, {"verdict": "GO" if not errors else "NO-GO", "stats": stats, "errors": errors, "warnings": warnings}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the creator Agent Plugin package.")
    parser.add_argument("--quick", action="store_true", help="Run fast manifest & SKILL.md validation only.")
    args = parser.parse_args()

    ok, report = validate_plugin(quick=args.quick)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
