# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A **GEO-SEO analysis toolkit** distributed as a suite of Claude Code skills + subagents + Python
scripts. "GEO" = Generative Engine Optimization — optimizing websites for AI search engines
(ChatGPT, Claude, Perplexity, Gemini, Google AI Overviews) rather than only traditional search.
Philosophy: **GEO-first, SEO-supported.**

This repo is the **source**. Users install it into `~/.claude/` (see [install](#install--uninstall)),
then invoke `/geo <command> <url>` inside Claude Code. Audits are run from the user's own working
directory and deliverables land there — never in this repo.

Deep documentation already lives in [`docs/`](docs/) — read it before large changes and keep it in
sync (per `CONTRIBUTING.md`):

| Topic | File |
|-------|------|
| Component architecture & data flow | `docs/architecture.md` |
| Composite GEO Score weights & formulas | `docs/scoring-methodology.md` |
| Skills / agents / scripts / schemas map | `docs/skills-and-agents.md` |
| Every `/geo` subcommand | `docs/commands-reference.md` |

## Repository layout

| Path | Contents |
|------|----------|
| `geo/SKILL.md` | Orchestrator — routes `/geo` subcommands, detects business type, fans out and synthesizes the audit |
| `skills/geo-*/` | 15 sub-skills (one `SKILL.md` each) — the reusable units and single-purpose subcommands |
| `agents/geo-*.md` | 5 parallel subagents launched during a full audit |
| `scripts/*.py` | Python analysis scripts (`fetch_page`, `citability_scorer`, `brand_scanner`, `llmstxt_generator`, `crm_dashboard`) |
| `scripts/webapp/` | Flask + HTMX CRM web UI (`app.py`) |
| `schema/*.json` | JSON-LD schema templates by business type |
| `templates/` | `geo-report-style.css` + `geo-report-template.html` for the PDF report |
| `docs/` | Long-form documentation (keep in sync with code) |
| `examples/` | Sample audit outputs, proposals, demo CRM data |
| `tests/` | Test suite (see [Testing](#testing)) |
| `white-label/` | Agency rebranding config (`brand_config.py`, `brand.example.json`) |
| `install.sh` / `install-win.sh` / `uninstall.sh` | Installers and uninstaller |

## Architecture (in brief)

Three layers — see `docs/architecture.md` for the full picture:

1. **Orchestrator** (`geo/SKILL.md`) routes subcommands, detects business type
   (SaaS / Local / E-commerce / Publisher / Agency / Other, which tailors recommendations), and
   for a full `/geo audit` fans out to subagents then synthesizes a composite **GEO Score (0-100)**.
2. **5 parallel subagents** (`agents/geo-*.md`) run simultaneously during an audit; each owns a
   slice (AI visibility, platform analysis, technical, content, schema) and writes a report section.
3. **15 sub-skills** (`skills/geo-*/`) are the reusable units the subagents invoke and the targets
   of single-purpose subcommands (`citability`, `crawlers`, `llmstxt`, …), plus the agency layer
   (`geo-prospect` CRM, `geo-proposal`, `geo-compare`, `geo-report-pdf`, `geo-update`).

**Two kinds of state:** audit deliverables are written to the user's current working directory;
agency/CRM data persists under `~/.geo-prospects/` (`prospects.json`, `audits/`, `proposals/`,
`reports/`), which the Python scripts and the Flask webapp read/write directly.

## Install / uninstall

`install.sh` copies `geo/`, `skills/`, `agents/`, `scripts/`, `schema/`, and `templates/` into
`~/.claude/`, creates a Python venv at `~/.claude/skills/geo/.venv` (using `uv` if available, else
stdlib `venv` + `pip`), installs `requirements.txt`, and **rewrites the script shebangs to point at
that venv**. That is why installed scripts run under `~/.claude/skills/geo/.venv/bin/python3` while
the scripts in this repo carry a portable `#!/usr/bin/env python3`. `uninstall.sh` reverses it.

## Running the scripts (from the repo)

Scripts print **JSON to stdout** so skills/agents can parse them — preserve that contract. Run them
with any Python that has `requirements.txt` installed (beautifulsoup4, requests, lxml, playwright,
Pillow, flask, rich, validators):

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
python3 -m playwright install chromium   # fetch_page.py uses Playwright for SSR/JS checks

python3 scripts/fetch_page.py <url>
python3 scripts/citability_scorer.py <url>
python3 scripts/brand_scanner.py "<brand name>"
python3 scripts/llmstxt_generator.py <url>
python3 scripts/crm_dashboard.py          # rich CLI over ~/.geo-prospects
python3 scripts/webapp/app.py             # CRM web UI at http://localhost:5050
```

## Testing

Tests are `unittest`-style (`tests/test_fetch_page_ssr.py`, using `unittest.mock` — no network):

```bash
python3 -m unittest discover -s tests -p 'test_*.py'   # all tests
python3 -m pytest tests/                                # or via pytest
python3 -m pytest tests/test_fetch_page_ssr.py -k ssr_content   # a single test
```

## Conventions

- **Docs stay in sync:** when changing code or behavior, update the matching file in `docs/`
  (a `CONTRIBUTING.md` requirement). Match existing structure and tone.
- **Commit messages:** imperative present tense, first line ≤ 72 chars, reference issues after.
- **Scripts → JSON stdout.** Keep the machine-readable output contract.
- Some code and docstrings are in Italian (e.g. `scripts/crm_dashboard.py`) — match the language of
  the file you edit.
- Crawl quality gates (from `geo/SKILL.md`): max 50 pages/audit, 30s fetch timeout, 1s delay between
  requests, max 5 concurrent, always respect robots.txt.
- Market-context stats and dates in `geo/SKILL.md` / `README.md` are editorial point-in-time content,
  not code.
- White-labeling for agencies is driven by `white-label/` — don't hardcode brand strings that belong
  in `brand.example.json`.
