# Fork Changelog — geo-seo-claude-plus

Downstream changes to [zubair-trabzada/geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude).

The upstream LICENSE and all existing skill / agent / script files are **unmodified**. This changelog records only fork-specific additions.

---

## 2026-05-16 — Fork inception

**Forked from upstream commit:** `5d8c0afe3b44bf9123f6849e97541f85eefabaca` ("Feature/isolated python venv linux/mac" — PR #48)
**Fork repo:** `stanleydansu/geo-seo-claude-plus`
**Fork maintainer:** Dan Su

### Added — 4 closure-loop skills

The fork adds four new skills that wire the existing audit/optimization skills into a closed 4-step GEO workflow (angles → publish → guide → measure):

| Skill | Path | Command | Closure-loop role |
| --- | --- | --- | --- |
| `geo-intent-matrix` | `skills/geo-intent-matrix/SKILL.md` | `/geo matrix <core-topic>` | Step 1 — Angles. 4-quadrant intent taxonomy + 12-week rolling schedule. Emits the intent-trigger vocabulary and form-binding contract consumed by the other three new skills. |
| `geo-citation-pipeline` | `skills/geo-citation-pipeline/SKILL.md` | `/geo pipeline <url>` | Step 3 — Guide. 5-stage pipeline (crawlers / internal-link wiring / AI-training authority backlinks / on-page compliance / rapid indexing) + Stage 6 cross-engine preferred-answer snapshot. Inherits from `geo-crawlers`, `geo-citability`, `geo-schema`, `geo-llmstxt`. |
| `geo-distribution-plan` | `skills/geo-distribution-plan/SKILL.md` | `/geo distribute <topic>` | Step 2 — Publish. Tier 1/2/3 platform scoring matrix, AI-training-corpus coverage tags, 14-day cadence, per-platform rewrite briefs (Zhihu / WeChat / Xiaohongshu / CSDN / Juejin / LinkedIn / Medium / Substack / Reddit / Hacker News / X / vertical media), 7/14/30-day reclaim checklist. Gated by `geo-citation-pipeline` returning PIPELINE_READY. |
| `geo-competitor-citation` | `skills/geo-competitor-citation/SKILL.md` | `/geo compete <my-domain> <c1,c2,...>` | Step 4 — Measure. 20 probes × 6 engines × 3 runs = 360-probe sweep. Produces 3-D gap matrix (brand × engine × intent) with verdict per quadrant and top-3 remediation plan. Reuses the intent taxonomy from `geo-intent-matrix`. |

### Modified — orchestrator routing

- `geo/SKILL.md`
  - Frontmatter `description` extended to mention the 4 new commands.
  - **Quick Reference table** — appended 4 new rows for `/geo matrix`, `/geo pipeline`, `/geo distribute`, `/geo compete`.
  - **Sub-Skills table** — renumbered title from "14 Specialized Components" to "19 Specialized Components"; added row 11 (`geo-report-pdf`, previously missing from the table) plus rows 16–19 for the 4 new skills.
  - **Output Files table** — appended 4 new rows mapping each new command to its output path under `~/.geo-prospects/`.
  - **Added section: Fork Extension: The GEO 4-Step Closure Loop** — ASCII diagram of the loop + a typical 6-step end-to-end example invocation.

### Added — attribution files

- `README.md`
  - Added top-section `## About This Fork` block (immediately after the banner, before the upstream content) describing the 4 new skills and linking to LICENSE / NOTICE / FORK_CHANGELOG.md.
  - Upstream `Quick Start`, `Commands`, `Architecture`, `Scoring Methodology`, and all other sections are unchanged.
- `NOTICE` — new file recording upstream copyright and license.
- `FORK_CHANGELOG.md` — this file.

### Unchanged (deliberately preserved)

- `LICENSE` — verbatim MIT, copyright Zubair Trabzada 2026.
- `install.sh` / `install-win.sh` / `uninstall.sh` — core install flow untouched. The fork does not add any new Python dependencies (all 4 new skills use the existing `requests`/`bs4`/WebFetch toolset).
- `requirements.txt` — unchanged.
- All existing `skills/geo-*/SKILL.md` files — unchanged.
- All `agents/geo-*.md` files — unchanged.
- All `scripts/*.py` files — unchanged.
- All `schema/*.json` files — unchanged.
- All `docs/`, `examples/`, `tests/` files — unchanged.
- `geo-update` skill — unchanged. `git pull upstream main` continues to work because the `upstream` remote still points at `zubair-trabzada/geo-seo-claude`.

### Runtime data layout (new directories under `~/.geo-prospects/`)

The new skills follow the upstream convention of writing runtime artifacts under `~/.geo-prospects/` (alongside `audits/`, `proposals/`, `reports/`):

```
~/.geo-prospects/
├── matrices/          # geo-intent-matrix output
├── pipelines/         # geo-citation-pipeline output
├── distribution/      # geo-distribution-plan output
├── competitor/        # geo-competitor-citation output
│   └── _runs/         # raw per-probe captures for reanalysis
└── (upstream dirs: audits/, proposals/, reports/, prospects.json)
```

These directories are created on first use by their respective skills. They are not removed by `uninstall.sh` (matching the upstream behavior for `~/.geo-prospects/`).

---

## Future changes

Append new entries here in reverse-chronological order. Each entry should include:

- Date
- Upstream commit hash if a rebase / merge from upstream occurred
- Files added / modified / removed
- Reason
