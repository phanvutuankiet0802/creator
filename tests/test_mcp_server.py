#!/usr/bin/env python3
"""End-to-end stdio JSON-RPC 2.0 tests for creator's Python MCP server."""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

PLUGIN_ROOT = pathlib.Path(__file__).resolve().parent.parent
SERVER_PY = PLUGIN_ROOT / "mcp-server" / "server.py"


class TestCreatorMCPServer(unittest.TestCase):
    def _send_session(self, requests: list[dict]) -> list[dict]:
        payload = "\n".join(json.dumps(r) for r in requests) + "\n"
        env = dict(os.environ)
        env["CREATOR_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
        proc = subprocess.run(
            [sys.executable, str(SERVER_PY)],
            input=payload,
            text=True,
            capture_output=True,
            timeout=20,
            env=env,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, f"Server exited non-zero: {proc.stderr}")
        lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
        return [json.loads(ln) for ln in lines]

    def test_initialize_and_list_tools_and_resources(self) -> None:
        resps = self._send_session(
            [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": 3, "method": "resources/list"},
            ]
        )
        self.assertEqual(len(resps), 3)
        self.assertEqual(resps[0]["result"]["serverInfo"]["name"], "creator-tools")
        tool_names = {t["name"] for t in resps[1]["result"]["tools"]}
        self.assertEqual(
            tool_names,
            {
                "qa_audit_python_file",
                "ui_check_wcag_contrast",
                "skill_validate_directory",
                "pm_analyze_blast_radius",
                "medical_search_pubmed",
                "medical_search_clinical_trials",
                "medical_search_openfda_drug",
            },
        )
        self.assertGreaterEqual(len(resps[2]["result"]["resources"]), 4)

    def test_wcag_contrast_positive_and_negative(self) -> None:
        resps = self._send_session(
            [
                {
                    "jsonrpc": "2.0",
                    "id": 10,
                    "method": "tools/call",
                    "params": {"name": "ui_check_wcag_contrast", "arguments": {"foreground_hex": "#111111", "background_hex": "#FFFFFF"}},
                },
                {
                    "jsonrpc": "2.0",
                    "id": 11,
                    "method": "tools/call",
                    "params": {"name": "ui_check_wcag_contrast", "arguments": {"foreground_hex": "#CCCCCC", "background_hex": "#FFFFFF"}},
                },
            ]
        )
        high = json.loads(resps[0]["result"]["content"][0]["text"])
        low = json.loads(resps[1]["result"]["content"][0]["text"])
        self.assertGreater(high["contrast_ratio"], 18.0)
        self.assertTrue(high["wcag_2_2"]["normal_text_aaa_7_0"])
        self.assertFalse(low["wcag_2_2"]["normal_text_aa_4_5"])

    def test_skill_validation_all_four_skills(self) -> None:
        reqs = []
        for idx, sk in enumerate(["thau-hieu", "creator-skill", "ui-ux", "qa-qc"], 1):
            reqs.append(
                {
                    "jsonrpc": "2.0",
                    "id": idx,
                    "method": "tools/call",
                    "params": {"name": "skill_validate_directory", "arguments": {"skill_dir": str(PLUGIN_ROOT / "skills" / sk)}},
                }
            )
        resps = self._send_session(reqs)
        for r in resps:
            data = json.loads(r["result"]["content"][0]["text"])
            self.assertEqual(data["verdict"], "GO", f"Skill failed validation: {data}")

    def test_qa_audit_catches_secret_leak_negative_case(self) -> None:
        synthetic_key = "sk-" + ("a1b2c3d4" * 3)
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write(f'API_KEY = "{synthetic_key}"\n')
            bad_path = tf.name
        try:
            resps = self._send_session(
                [
                    {
                        "jsonrpc": "2.0",
                        "id": 20,
                        "method": "tools/call",
                        "params": {"name": "qa_audit_python_file", "arguments": {"file_path": bad_path}},
                    }
                ]
            )
            data = json.loads(resps[0]["result"]["content"][0]["text"])
            self.assertEqual(data["verdict"], "NO-GO")
            self.assertIn("openai_or_api_key", data["secret_leaks"])
        finally:
            os.unlink(bad_path)

    def test_phi_guard_blocks_patient_identifiers(self) -> None:
        resps = self._send_session(
            [
                {
                    "jsonrpc": "2.0",
                    "id": 30,
                    "method": "tools/call",
                    "params": {
                        "name": "medical_search_pubmed",
                        "arguments": {"query": "hypertension patient@example.com MRN:998877"},
                    },
                },
                {
                    "jsonrpc": "2.0",
                    "id": 31,
                    "method": "tools/call",
                    "params": {
                        "name": "medical_search_openfda_drug",
                        "arguments": {"drug_name": "metformin SSN 123-45-6789"},
                    },
                },
            ]
        )
        for r in resps:
            self.assertTrue(r["result"]["isError"])
            data = json.loads(r["result"]["content"][0]["text"])
            self.assertTrue(data["blocked"])
            self.assertTrue(len(data["detected_patterns"]) >= 1)

    def test_pm_blast_radius_and_resource_read(self) -> None:
        resps = self._send_session(
            [
                {
                    "jsonrpc": "2.0",
                    "id": 40,
                    "method": "tools/call",
                    "params": {"name": "pm_analyze_blast_radius", "arguments": {"root_dir": str(PLUGIN_ROOT), "target_symbol": "HealthBench"}},
                },
                {
                    "jsonrpc": "2.0",
                    "id": 41,
                    "method": "resources/read",
                    "params": {"uri": "creator://tokens/base-design-tokens"},
                },
            ]
        )
        br = json.loads(resps[0]["result"]["content"][0]["text"])
        self.assertGreaterEqual(br["python_modules_count"], 18)
        self.assertGreaterEqual(len(br["impacted_files"]), 3)
        res_txt = resps[1]["result"]["contents"][0]["text"]
        self.assertIn("wcag-version", res_txt)


if __name__ == "__main__":
    unittest.main(verbosity=2)
