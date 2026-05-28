---
name: geo-update
description: Pull the latest GEO-SEO skill updates from the upstream repository. Compares installed files against the latest release, shows what changed, and updates all skills, agents, scripts, and schema templates in place.
allowed-tools:
  - Bash
  - Read
  - Write
---

# GEO-SEO Update Skill

## Purpose

Updates the locally installed GEO-SEO skills, agents, scripts, and schema templates to the latest version from the upstream repository. Shows a summary of what changed before and after the update.

---

## Update Workflow

### Step 1: Determine Installed Location

The GEO-SEO toolkit installs to these locations under `~/.claude/`:

| Component | Install Path |
|-----------|-------------|
| Main skill | `~/.claude/skills/geo/` |
| Sub-skills | `~/.claude/skills/geo-*/` |
| Agents | `~/.claude/agents/geo-*.md` |
| Scripts | `~/.claude/skills/geo/scripts/` |
| Schema templates | `~/.claude/skills/geo/schema/` |
| Hooks | `~/.claude/skills/geo/hooks/` |

Verify the installation exists by checking for `~/.claude/skills/geo/SKILL.md`. If it does not exist, inform the user that GEO-SEO is not installed and suggest running the installer instead.

### Step 2: Clone Latest from Upstream

```bash
TEMP_DIR=$(mktemp -d)
git clone --depth 1 https://github.com/zubair-trabzada/geo-seo-claude.git "$TEMP_DIR/repo"
```

If the clone fails, report the error and stop. Do not modify any installed files.

### Step 3: Compare Installed vs Latest

Before copying files, generate a diff summary so the user knows what will change:

1. For each component directory, compare the installed files against the cloned files using `diff --recursive --brief`.
2. Categorise changes as:
   - **New files** — exist in upstream but not locally
   - **Modified files** — exist in both but differ
   - **Removed files** — exist locally but not in upstream (these are NOT deleted automatically)
3. Present the summary to the user.

### Step 4: Apply Updates

Copy files from the cloned repo over the installed locations:

```bash
CLAUDE_DIR="${HOME}/.claude"
SOURCE_DIR="$TEMP_DIR/repo"

# Main skill
cp -r "$SOURCE_DIR/geo/"* "$CLAUDE_DIR/skills/geo/"

# Sub-skills
for skill_dir in "$SOURCE_DIR/skills"/*/; do
    skill_name=$(basename "$skill_dir")
    mkdir -p "$CLAUDE_DIR/skills/${skill_name}"
    cp -r "$skill_dir"* "$CLAUDE_DIR/skills/${skill_name}/"
done

# Agents
for agent_file in "$SOURCE_DIR/agents/"*.md; do
    cp "$agent_file" "$CLAUDE_DIR/agents/"
done

# Scripts
if [ -d "$SOURCE_DIR/scripts" ]; then
    cp -r "$SOURCE_DIR/scripts/"* "$CLAUDE_DIR/skills/geo/scripts/"
    chmod +x "$CLAUDE_DIR/skills/geo/scripts/"*.py 2>/dev/null || true
fi

# Schema templates
if [ -d "$SOURCE_DIR/schema" ]; then
    cp -r "$SOURCE_DIR/schema/"* "$CLAUDE_DIR/skills/geo/schema/"
fi

# Hooks
if [ -d "$SOURCE_DIR/hooks" ] && [ "$(ls -A "$SOURCE_DIR/hooks" 2>/dev/null)" ]; then
    mkdir -p "$CLAUDE_DIR/skills/geo/hooks"
    cp -r "$SOURCE_DIR/hooks/"* "$CLAUDE_DIR/skills/geo/hooks/"
    chmod +x "$CLAUDE_DIR/skills/geo/hooks/"* 2>/dev/null || true
fi
```

### Step 5: Update Python Dependencies

If `requirements.txt` exists in the upstream repo and differs from the installed version:

```bash
python3 -m pip install -r "$SOURCE_DIR/requirements.txt" --quiet
```

Report any failures but do not treat them as fatal.

### Step 6: Clean Up

```bash
rm -rf "$TEMP_DIR"
```

### Step 7: Report Results

Present a summary:

```
GEO-SEO Update Complete
=======================
New files:      [count]
Modified files: [count]
Unchanged:      [count]
Removed upstream (kept locally): [count]

Dependencies: [updated / unchanged / failed]
```

If there were removed files upstream, list them and suggest the user review whether to delete them manually.

---

## Important Notes

- **Never delete locally installed files** that no longer exist upstream. The user may have customised them. List them and let the user decide.
- **Never modify `~/.claude/settings.json` or `~/.claude/settings.local.json`** — these are user configuration files, not part of the GEO-SEO toolkit.
- **If already up to date** (no diff), report that and skip the copy step.
- **Restart notice:** Remind the user that skill changes take effect in new Claude Code sessions. They should restart their session to use the updated skills.
