# `creator` — Dual-Standard Agent Plugin (Core Engineering + Clinical AI Suite)

`creator` là gói **Agent Plugin Cấp 3** tuân thủ chuẩn mở **[Agent Plugins 1.0.0](https://developers.googleblog.com/agent-plugins-package-your-skills-tools-and-more/)** (Google/Antigravity, OpenAI Codex, Cursor, Microsoft) đồng thời tương thích song song với **Claude Code Plugin** (`.claude-plugin/`).

Gói tích hợp **4 Skills đa năng nạp theo ngữ cảnh (Progressive Disclosure)**, **4 hồ sơ Subagent**, **1 Python MCP Server không cần cài thư viện ngoài** (7 công cụ kỹ thuật & tra cứu bằng chứng y khoa có khóa bảo vệ PHI/PII), cùng **mẫu kết nối HL7 FHIR R4** và **GitHub Actions CI**.

---

## Cấu Trúc Gói

```text
creator/
├── plugin.json                         # Manifest chuẩn Agent Plugins 1.0.0
├── mcp.json                            # Khai báo MCP stdio server (chạy sẵn với Python 3.10+)
├── mcp.fhir.example.json               # Mẫu mở rộng HL7 FHIR R4 (dùng biến môi trường, 0 bí mật)
├── .claude-plugin/                     # Lớp tương thích song song cho Claude Code
├── .agents/plugins/marketplace.json    # Catalog cài đặt cho repo / local marketplace
├── .github/workflows/validate-plugin.yml
├── skills/
│   ├── thau-hieu/                      # Bộ định tuyến phân rã 4 câu hỏi (ADaPT/RouteGoT)
│   ├── creator-skill/                  # Tổng công trình sư 4-Stream & 15 Python validators
│   ├── ui-ux/                          # W3C DTCG Tokens, WCAG 2.2 AA/AAA, NHS Clinical UX
│   └── qa-qc/                          # Zero-User-Tester, Tháp QA 6 tầng, HealthBench Rubric
├── mcp-server/server.py                # Stdio JSON-RPC 2.0 MCP Server (7 tools + 4 resources)
├── agents/                             # 4 subagent roles (task-router, skill-architect, ui-ux-auditor, independent-qa)
├── hooks/hooks.json                    # Lifecycle hook kiểm định nhanh sau khi chỉnh sửa
├── scripts/validate_plugin.py          # Công cụ kiểm định toàn bộ plugin & skills
└── tests/test_mcp_server.py            # Bộ test E2E giao thức stdio MCP (dương tính + âm tính + PHI guard)
```

---

## 7 Công Cụ MCP Tích Hợp (`creator-tools`)

| Công cụ MCP | Nhóm | Chức năng |
| :--- | :--- | :--- |
| `qa_audit_python_file` | QA / Security | Quét AST, phát hiện lỗi bảo mật, rò rỉ API key/secret & cảnh báo PHI trên mã Python |
| `ui_check_wcag_contrast` | UI / UX | Tính chính xác tỷ lệ tương phản quang học W3C WCAG 2.2 AA/AAA giữa 2 mã màu hex |
| `skill_validate_directory` | Skill Architect | Kiểm định bất kỳ thư mục Skill nào theo đặc tả `agentskills.io` (`< 500` dòng, refs 1 cấp, AST/JSON) |
| `pm_analyze_blast_radius` | PM / Architect | Thống kê cấu trúc kho mã, định nghĩa hàm/class Python và truy vết bán kính ảnh hưởng |
| `medical_search_pubmed` | Y khoa (EBM) | Tra cứu PubMed E-utilities có **PHI/PII Guard** chặn định danh bệnh nhân trước khi gửi ra ngoài |
| `medical_search_clinical_trials` | Y khoa (EBM) | Tra cứu thử nghiệm lâm sàng ClinicalTrials.gov v2 (NCT ID, phase, status) có **PHI Guard** |
| `medical_search_openfda_drug` | Y khoa (EBM) | Tra cứu nhãn thuốc OpenFDA (boxed warnings, chỉ định, chống chỉ định, liều) có **PHI Guard** |

---

## Cài Đặt & Sử Dụng

### 1. Kiểm định cục bộ trước khi dùng / đẩy GitHub
```bash
python3 scripts/validate_plugin.py
python3 -m unittest discover -s tests -p "test_*.py" -v
```

### 2. Cài đặt trực tiếp từ GitHub (Antigravity / Codex / Claude Code / Cursor)
```bash
git clone https://github.com/phanvutuankiet0802/creator.git
```
GitHub Actions (`.github/workflows/validate-plugin.yml`) tự động chạy bộ kiểm định manifest, skills và MCP server trên mỗi lần push/PR.

### 3. Kết nối trong Antigravity & Các Client Hỗ Trợ Agent Plugins 1.0.0
- **Antigravity IDE / CLI & Gemini CLI:** Trỏ thư mục plugin tới `./creator` (hoặc cài từ repo GitHub của bạn qua `plugin.json` / `.agents/plugins/marketplace.json`). Các skill trong `skills/` cũng đã tương thích trực tiếp với thư mục `.gemini/skills/`.
- **Claude Code:** Hỗ trợ trực tiếp qua `.claude-plugin/plugin.json` và `.claude-plugin/marketplace.json` (`claude --plugin-dir ./creator`).
- **OpenAI Codex / Cursor:** Đọc trực tiếp `plugin.json`, `mcp.json` và `.agents/plugins/marketplace.json`.

### 4. Mở rộng kết nối HL7 FHIR R4 (Tùy chọn cho dự án Y tế)
Xem mẫu `mcp.fhir.example.json`, cấu hình `FHIR_MCP_SERVER_URL` và `FHIR_MCP_ACCESS_TOKEN` bằng biến môi trường — **tuyệt đối không lưu token hay dữ liệu định danh bệnh nhân (PHI) trong tệp JSON hoặc kho Git**.
