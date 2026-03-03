# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Imbryk, please report it by opening a GitHub Security Advisory rather than a public issue.

---

## Dependency Audit

Last audited: 2026-03-03 (issue #3)

### npm (JavaScript/TypeScript)

All known critical and high vulnerabilities in direct npm dependencies have been addressed. See the table below for the key changes made.

| Package | Previous | Updated | Reason |
|---|---|---|---|
| `jsdom` | `~22.1.0` | `^25.0.0` | CVE-2024-21538 (XSS via DOM clobbering), prototype pollution; fix is in jsdom 25.x |
| `prettier` | `^2.6.2` | `^3.0.0` | Prettier 2.x is EOL; ReDoS in CSS/SCSS parser via crafted input |

Transitive dependencies audited: `tough-cookie`, `cross-spawn`, `braces`, `micromatch`, `semver`, `word-wrap`, `@babel/traverse`, `follow-redirects`, `postcss`, `nth-check`, `express` (with `body-parser`, `send`, `serve-static`), `node-fetch`, `esbuild`, `rollup`, `ws` — all resolved to patched versions in `package-lock.json`.

---

### Python — ingestion-api (`apps/ingestion-api/pyproject.toml`)

| Package | Previous | Updated | Reason |
|---|---|---|---|
| `sqlalchemy` | `>=2.0` | `>=2.0.36` | Tightened lower bound; avoids unnecessarily old 2.0.x releases |
| `alembic` | `>=1.13` | `>=1.13.3` | Tightened lower bound to latest 1.13.x patch |
| `slowapi` | `>=0.1` | `>=0.1.9` | Versions <0.1.5 allow rate-limit bypass via X-Forwarded-For header manipulation; 0.1.9 is the latest release |
| `braintree` | `>=4.0` | `>=4.30.0` | Early 4.0.x versions carry older `requests` transitive constraints; `requests` had CVE-2023-32681 (auth header leak on redirect, fixed in requests 2.31.0). Recent braintree 4.x pins a patched requests version. |

No known CVEs in `fastapi`, `pydantic`, `uvicorn`, `google-cloud-aiplatform`, or `sentry-sdk` within the versions specified (current lower bounds are already well above all known vulnerability thresholds for these packages).

---

### Python — newsroom-director (`apps/newsroom-director/pyproject.toml`)

| Package | Previous | Updated | Reason |
|---|---|---|---|
| `torch` (Linux / macOS ARM64) | `>=2.4` | `>=2.6.0` | **CVE-2025-32434** (Critical, CVSS 9.3) — arbitrary code execution via `torch.load()` even with `weights_only=True`. The `weights_only` protection added in PyTorch 2.4.0 was bypassed by this vulnerability. Fixed in PyTorch 2.6.0. |
| `numpy` | `<2` | `>=1.24,<2` | Added lower bound; versions <1.22.0 carry CVE-2021-41496 (buffer overflow) and CVE-2021-34141 (string comparison vulnerability). NumPy 1.24 (Nov 2022) is the baseline for secure 1.x usage. |
| `sqlalchemy` | `>=2.0` | `>=2.0.36` | Same as ingestion-api — tightened lower bound |
| `alembic` | `>=1.13` | `>=1.13.3` | Same as ingestion-api — tightened lower bound |

---

## Accepted Risks

### torch on macOS x86_64 (Intel Mac) — MEDIUM risk, development only

**Constraint:** `torch>=2.1,<2.3; sys_platform == 'darwin' and platform_machine == 'x86_64'`

**Unpatched CVEs:**
- **CVE-2024-5480** (High, CVSS 8.8) — Arbitrary code execution via `torch.load()` without `weights_only=True`. Fixed in PyTorch 2.4.0. The `<2.3` cap cannot be raised because PyTorch dropped official binary distribution for macOS x86_64 (Intel Mac) after 2.2.x.
- **CVE-2025-32434** (Critical, CVSS 9.3) — Arbitrary code execution via `torch.load()` even with `weights_only=True`. Fixed in PyTorch 2.6.0. Same constraint: cannot be raised for Intel Mac.

**Risk assessment:** Intel Mac support is a developer convenience only — the production deployment target is Linux (Cloud Run). These CVEs require loading a maliciously crafted model file. In the Imbryk newsroom-director, the only models loaded via `torch.load` are:
- The sentence-transformer model (`all-MiniLM-L6-v2` or similar) downloaded from the Hugging Face Hub over HTTPS with SHA256 checksums

**Mitigations in place:**
- Model files are downloaded from the official Hugging Face Hub only (HTTPS, with hash verification by the `transformers` library)
- No user-supplied or externally-sourced model files are ever loaded
- Production runs on Linux where the `>=2.6.0` constraint applies and CVE-2025-32434 is patched

**Recommendation:** Intel Mac developers should ensure they only load models from official Hugging Face repositories and never load `.pt`/`.pth` files from untrusted sources. If Intel Mac developer support is no longer required, remove the `sys_platform == 'darwin' and platform_machine == 'x86_64'` conditional lines.

---

## Recommended CI Additions

The following tooling should be added to CI to catch new vulnerabilities automatically:

- **npm:** Add `npm audit --audit-level=high` as a gating CI step
- **Python:** Add `pip-audit` (pip-audit.readthedocs.io) or `osv-scanner` (google/osv-scanner) as a CI step against `uv.lock` or `pip freeze` output
- **Dependabot or Renovate:** Configure automated PRs for security advisories on both npm and Python ecosystems
