# Getting Started

## Prerequisites

| Requirement | Why it's needed |
|---|---|
| Python 3.8+ | Runs the utility scripts (page fetching, citability scoring, PDF generation, etc.) |
| Claude Code CLI | The skills and agents are loaded and invoked through Claude Code |
| Git | Used by the installer to clone the repository |
| Playwright (optional) | Enables screenshot capture; install separately after the main install |

Install Claude Code if you haven't already:

```bash
npm install -g @anthropic-ai/claude-code
```

---

## Installation

### macOS / Linux — one-liner

```bash
curl -fsSL https://raw.githubusercontent.com/zubair-trabzada/geo-seo-claude/main/install.sh | bash
```

### macOS / Linux — manual

```bash
git clone https://github.com/zubair-trabzada/geo-seo-claude.git
cd geo-seo-claude
./install.sh
```

### Windows — Git Bash

PowerShell and Command Prompt are not supported. You must use [Git Bash](https://git-scm.com/downloads) (included with Git for Windows).

```bash
# One-liner (run from Git Bash)
curl -fsSL https://raw.githubusercontent.com/zubair-trabzada/geo-seo-claude/main/install-win.sh | bash

# Manual
git clone https://github.com/zubair-trabzada/geo-seo-claude.git
cd geo-seo-claude
./install-win.sh
```

Right-click the cloned folder and choose "Open Git Bash here", or navigate to it inside an existing Git Bash session.

### What the installer does

- Copies the `geo` orchestrator skill to `~/.claude/skills/geo/`
- Copies 13 sub-skills to `~/.claude/skills/geo-*/`
- Copies 5 subagent definitions to `~/.claude/agents/`
- Installs Python dependencies via `pip install --user`
- Optionally installs the Playwright Chromium browser for screenshots

---

## Verify the Install

After installation, open Claude Code in any project directory and run:

```
/geo quick https://example.com
```

If the skill is wired up correctly, Claude Code will start a 60-second GEO visibility snapshot. If you see "unknown command" or nothing happens, restart Claude Code — it reads skills and agents at startup.

To confirm the files landed in the right place:

```bash
ls ~/.claude/skills/geo/
ls ~/.claude/skills/ | grep geo
ls ~/.claude/agents/ | grep geo
```

---

## Your First Audit

### Quick path — 60-second snapshot

```
/geo quick https://yoursite.com
```

Returns a high-level GEO visibility score and the top issues. Good for a first look or a fast client check.

### Full path — complete audit

```
/geo audit https://yoursite.com
```

Launches 5 parallel subagents covering AI visibility, platform optimization, technical SEO, content quality, and structured data. Produces a prioritized action plan with a composite GEO score (0–100).

The full audit takes several minutes depending on the site. See [scoring-methodology.md](scoring-methodology.md) for how the score is calculated and [commands-reference.md](commands-reference.md) for all available commands.

---

## Troubleshooting

**Python not found during install**
- Symptom: installer exits with `Python 3.8+ is required but not found`
- Cause: Python is not installed or not on `PATH`
- Fix: install from [python.org](https://www.python.org/downloads/); on Windows check "Add Python to PATH" during setup; then reopen your terminal

**Claude Code CLI not found**
- Symptom: installer warns `Claude Code CLI not found in PATH`
- Cause: `claude` is not installed or not on `PATH`
- Fix: `npm install -g @anthropic-ai/claude-code`; confirm with `claude --version`

**Skills not showing up in Claude Code**
- Symptom: `/geo quick` produces "unknown command" or no response
- Cause: Claude Code reads skills at startup; it won't see files added after launch
- Fix: fully quit and reopen Claude Code

**Permission denied on `./install.sh`**
- Symptom: `bash: ./install.sh: Permission denied`
- Cause: execute bit not set
- Fix: `chmod +x install.sh && ./install.sh`

**Wrong shell on Windows**
- Symptom: `curl` not recognized, or script syntax errors
- Cause: running `install-win.sh` in PowerShell or Command Prompt
- Fix: use Git Bash only — right-click the folder, "Open Git Bash here"

**Playwright not available / screenshots missing**
- Symptom: screenshot-related steps silently skip or error
- Cause: Playwright was skipped during install (non-interactive or answered no)
- Fix: install it manually:
  ```bash
  python3 -m playwright install chromium
  ```

**Python dependencies failed during install**
- Symptom: installer prints `Some Python dependencies failed to install`
- Cause: pip error (network, permissions, or virtualenv conflict)
- Fix: run manually from the cloned repo or from `~/.claude/skills/geo/`:
  ```bash
  python3 -m pip install --user -r requirements.txt
  ```

---

## Uninstall

### Scripted

Run from the cloned repository directory:

```bash
./uninstall.sh
```

This removes `~/.claude/skills/geo/`, all `~/.claude/skills/geo-*/` sub-skills, and all `~/.claude/agents/geo-*.md` agent files. Python packages are not removed.

### Manual

```bash
rm -rf ~/.claude/skills/geo ~/.claude/skills/geo-* ~/.claude/agents/geo-*.md
```

### Runtime data

The directory `~/.geo-prospects/` (used by `/geo prospect`, `/geo proposal`, and `/geo compare`) is **not** removed by the uninstaller. Delete it manually if you no longer need the data:

```bash
rm -rf ~/.geo-prospects
```

---

See also: [architecture.md](architecture.md) | [commands-reference.md](commands-reference.md) | [scoring-methodology.md](scoring-methodology.md) | [skills-and-agents.md](skills-and-agents.md)
