#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# GEO-SEO Claude Code Skill Installer
# Installs the GEO-first SEO analysis tool for Claude Code
# with an isolated Python virtual environment.
# ============================================================

REPO_URL="https://github.com/zubair-trabzada/geo-seo-claude.git"
CLAUDE_DIR="${HOME}/.claude"
SKILLS_DIR="${CLAUDE_DIR}/skills"
AGENTS_DIR="${CLAUDE_DIR}/agents"
INSTALL_DIR="${SKILLS_DIR}/geo"
VENV_DIR="${INSTALL_DIR}/.venv"
VENV_PY="${VENV_DIR}/bin/python3"
# Tilde-form path for patched references inside skill/agent .md files.
# The tilde is intentionally kept literal — Claude Code's Bash expands
# it when running the command later. Do NOT replace with $HOME here.
# shellcheck disable=SC2088
VENV_MD_PY='~/.claude/skills/geo/.venv/bin/python3'
TEMP_DIR=$(mktemp -d)

# Detect if running via curl pipe (no interactive input available)
INTERACTIVE=true
if [ ! -t 0 ]; then
    INTERACTIVE=false
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   GEO-SEO Claude Code Skill Installer    ║${NC}"
    echo -e "${BLUE}║   GEO-First AI Search Optimization       ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_error()   { echo -e "${RED}✗ $1${NC}"; }
print_info()    { echo -e "${BLUE}→ $1${NC}"; }

cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# Cross-platform in-place sed (GNU sed and BSD/macOS sed).
# Writes a .bak sibling then removes it.
sed_inplace() {
    local pattern="$1"
    local file="$2"
    sed -i.bak "$pattern" "$file" && rm -f "${file}.bak"
}

main() {
    print_header

    # ---- Check Prerequisites ----
    print_info "Checking prerequisites..."

    if ! command -v git &> /dev/null; then
        print_error "Git is required but not installed."
        echo "  Install: https://git-scm.com/downloads"
        exit 1
    fi
    print_success "Git found: $(git --version)"

    PYTHON_CMD=""
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PY_VERSION=$(python --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        if [ -n "$PY_VERSION" ]; then
            MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
            MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
            if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 8 ]; then
                PYTHON_CMD="python"
            fi
        fi
    fi

    if [ -z "$PYTHON_CMD" ]; then
        print_error "Python 3.8+ is required but not found."
        echo "  Install: https://www.python.org/downloads/"
        exit 1
    fi
    print_success "Python found: $($PYTHON_CMD --version)"

    if ! command -v claude &> /dev/null; then
        print_warning "Claude Code CLI not found in PATH."
        echo "  This tool requires Claude Code to function."
        echo "  Install: npm install -g @anthropic-ai/claude-code"
        echo ""
        if [ "$INTERACTIVE" = true ]; then
            read -p "Continue installation anyway? (y/n): " -n 1 -r
            echo ""
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        else
            print_info "Non-interactive mode — continuing anyway..."
        fi
    else
        print_success "Claude Code CLI found"
    fi

    # Detect uv for faster venv/install (optional, falls back to stdlib venv + pip)
    USE_UV=false
    if command -v uv &> /dev/null; then
        USE_UV=true
        print_success "'uv' detected — will use it for a faster install"
    fi

    # ---- Create Directories ----
    print_info "Creating directories..."

    mkdir -p "$SKILLS_DIR" "$AGENTS_DIR" "$INSTALL_DIR"
    mkdir -p "$INSTALL_DIR/scripts" "$INSTALL_DIR/schema" "$INSTALL_DIR/hooks"

    print_success "Directory structure created"

    # ---- Resolve source directory (local checkout or clone) ----
    print_info "Fetching GEO-SEO skill files..."

    SCRIPT_DIR=""
    if [ -n "${BASH_SOURCE[0]:-}" ] && [ "${BASH_SOURCE[0]}" != "bash" ]; then
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)" || true
    fi

    if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/geo/SKILL.md" ]; then
        print_info "Installing from local directory..."
        SOURCE_DIR="$SCRIPT_DIR"
    else
        print_info "Cloning from repository..."
        git clone --depth 1 "$REPO_URL" "$TEMP_DIR/repo" || {
            print_error "Failed to clone repository. Check your internet connection."
            exit 1
        }
        SOURCE_DIR="${TEMP_DIR}/repo"
    fi

    # ---- Install Main Skill ----
    print_info "Installing main GEO skill..."
    cp -r "$SOURCE_DIR/geo/"* "$INSTALL_DIR/"
    print_success "Main skill installed → ${INSTALL_DIR}/"

    # ---- Install Sub-Skills ----
    print_info "Installing sub-skills..."
    SKILL_COUNT=0
    for skill_dir in "$SOURCE_DIR/skills"/*/; do
        if [ -d "$skill_dir" ]; then
            skill_name=$(basename "$skill_dir")
            target_dir="${SKILLS_DIR}/${skill_name}"
            mkdir -p "$target_dir"
            cp -r "$skill_dir"* "$target_dir/"
            SKILL_COUNT=$((SKILL_COUNT + 1))
            print_success "  ${skill_name}"
        fi
    done
    echo "  → ${SKILL_COUNT} sub-skills installed"

    # ---- Install Agents ----
    print_info "Installing subagents..."
    AGENT_COUNT=0
    for agent_file in "$SOURCE_DIR/agents/"*.md; do
        if [ -f "$agent_file" ]; then
            cp "$agent_file" "$AGENTS_DIR/"
            AGENT_COUNT=$((AGENT_COUNT + 1))
            print_success "  $(basename "$agent_file")"
        fi
    done
    echo "  → ${AGENT_COUNT} subagents installed"

    # ---- Install Scripts ----
    print_info "Installing utility scripts..."
    if [ -d "$SOURCE_DIR/scripts" ]; then
        cp -r "$SOURCE_DIR/scripts/"* "$INSTALL_DIR/scripts/"
        print_success "Scripts installed → ${INSTALL_DIR}/scripts/"
    fi

    # ---- Install Schema Templates ----
    print_info "Installing schema templates..."
    if [ -d "$SOURCE_DIR/schema" ]; then
        cp -r "$SOURCE_DIR/schema/"* "$INSTALL_DIR/schema/"
        print_success "Schema templates installed → ${INSTALL_DIR}/schema/"
    fi

    # ---- Install Hooks ----
    if [ -d "$SOURCE_DIR/hooks" ] && [ "$(ls -A "$SOURCE_DIR/hooks" 2>/dev/null)" ]; then
        print_info "Installing hooks..."
        cp -r "$SOURCE_DIR/hooks/"* "$INSTALL_DIR/hooks/"
        chmod +x "$INSTALL_DIR/hooks/"* 2>/dev/null || true
        print_success "Hooks installed → ${INSTALL_DIR}/hooks/"
    fi

    # ---- Create Virtual Environment ----
    print_info "Creating isolated Python environment → ${VENV_DIR}"

    # If an old venv is lying around from a previous install, replace it.
    rm -rf "$VENV_DIR"

    if [ "$USE_UV" = true ]; then
        uv venv "$VENV_DIR" --python "$PYTHON_CMD" --quiet || {
            print_error "uv venv creation failed."
            exit 1
        }
    else
        if ! $PYTHON_CMD -m venv "$VENV_DIR" 2>/dev/null; then
            print_error "Failed to create virtual environment."
            echo ""
            echo "  Your Python may be missing the 'venv' module. Try one of:"
            echo "    • Debian/Ubuntu:  sudo apt install python3-venv"
            echo "    • Fedora/RHEL:    sudo dnf install python3-virtualenv"
            echo "    • Install 'uv':   https://docs.astral.sh/uv/  (no system packages needed)"
            exit 1
        fi
    fi
    print_success "Virtual environment created"

    # ---- Install Python Dependencies into the venv ----
    print_info "Installing Python dependencies into venv..."

    if [ ! -f "$SOURCE_DIR/requirements.txt" ]; then
        print_warning "requirements.txt missing — skipping dependency install."
    elif [ "$USE_UV" = true ]; then
        uv pip install --python "$VENV_PY" -r "$SOURCE_DIR/requirements.txt" --quiet || {
            print_error "Failed to install dependencies via uv."
            exit 1
        }
    else
        "$VENV_PY" -m pip install --upgrade pip --quiet
        "$VENV_PY" -m pip install -r "$SOURCE_DIR/requirements.txt" --quiet || {
            print_error "Failed to install dependencies."
            exit 1
        }
    fi
    print_success "Dependencies installed (isolated — nothing on system Python)"

    # Keep a copy of requirements.txt next to the venv for reference.
    cp "$SOURCE_DIR/requirements.txt" "$INSTALL_DIR/" 2>/dev/null || true

    # ---- Rewrite script shebangs to the venv interpreter ----
    print_info "Pinning script shebangs to venv interpreter..."
    SHEBANG_COUNT=0
    for f in "$INSTALL_DIR/scripts/"*.py; do
        [ -f "$f" ] || continue
        sed_inplace "1s|^#!.*|#!${VENV_PY}|" "$f"
        chmod +x "$f"
        SHEBANG_COUNT=$((SHEBANG_COUNT + 1))
    done
    print_success "${SHEBANG_COUNT} script(s) pinned to venv"

    # ---- Patch skill & agent markdown references ----
    # Strategy:
    #   1. "python3 ~/.claude/skills/geo/scripts/"  →  "~/.claude/skills/geo/scripts/"
    #      (scripts now self-execute via their shebang)
    #   2. bare "python3 -c " / "python3 -m "  →  "<venv>/python3 -c " / " -m "
    #      (inline snippets still need the venv interpreter for requests/etc.)
    print_info "Rewriting skill & agent references to use the venv..."

    patch_md() {
        local f="$1"
        sed_inplace 's|python3 ~/\.claude/skills/geo/scripts/|~/.claude/skills/geo/scripts/|g' "$f"
        sed_inplace "s|python3 -c |${VENV_MD_PY} -c |g" "$f"
        sed_inplace "s|python3 -m |${VENV_MD_PY} -m |g" "$f"
    }

    PATCH_COUNT=0
    for f in "$INSTALL_DIR/SKILL.md" "$SKILLS_DIR"/geo-*/SKILL.md "$AGENTS_DIR"/geo-*.md; do
        if [ -f "$f" ]; then
            patch_md "$f"
            PATCH_COUNT=$((PATCH_COUNT + 1))
        fi
    done
    print_success "${PATCH_COUNT} markdown file(s) rewritten"

    # ---- Optional: Install Playwright browsers ----
    if [ "$INTERACTIVE" = true ]; then
        echo ""
        read -p "Install Playwright browsers for screenshots? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Installing Playwright Chromium into venv..."
            if "$VENV_PY" -m playwright install chromium 2>/dev/null; then
                print_success "Playwright Chromium installed"
            else
                print_warning "Playwright install failed — screenshots won't be available."
                echo "  Retry: ${VENV_PY} -m playwright install chromium"
            fi
        fi
    else
        print_info "Skipping Playwright (non-interactive). Run later:"
        echo "    ${VENV_PY} -m playwright install chromium"
    fi

    # ---- Verify Installation ----
    echo ""
    print_info "Verifying installation..."
    VERIFY_OK=true

    verify() {
        local label="$1"
        shift
        if "$@"; then
            print_success "$label"
        else
            print_error "$label missing"
            VERIFY_OK=false
        fi
    }

    # Count agent files via glob (no ls parsing).
    agent_count=0
    for f in "$AGENTS_DIR"/geo-*.md; do
        [ -f "$f" ] && agent_count=$((agent_count + 1))
    done

    verify "Main skill file"       test -f "$INSTALL_DIR/SKILL.md"
    verify "Sub-skills directory"  test -d "$SKILLS_DIR/geo-audit"
    verify "Agent files"           test "$agent_count" -gt 0
    verify "Utility scripts"       test -d "$INSTALL_DIR/scripts"
    verify "Schema templates"      test -d "$INSTALL_DIR/schema"
    verify "Venv interpreter"      test -x "$VENV_PY"

    if [ "$VERIFY_OK" = false ]; then
        echo ""
        print_warning "One or more files are missing. The install may be incomplete."
    fi

    # ---- Print Summary ----
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║        Installation Complete!             ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
    echo ""
    echo "  Installed to: ${INSTALL_DIR}"
    echo "  Venv:         ${VENV_DIR}"
    echo "  Skills:       ${SKILL_COUNT} sub-skills"
    echo "  Agents:       ${AGENT_COUNT} subagents"
    echo ""
    echo -e "${BLUE}Quick Start:${NC}"
    echo "  Open Claude Code and try:"
    echo ""
    echo "    /geo audit https://example.com"
    echo "    /geo quick https://example.com"
    echo "    /geo citability https://example.com/blog/article"
    echo "    /geo crawlers https://example.com"
    echo "    /geo report https://example.com"
    echo ""
    echo -e "${BLUE}Available Commands:${NC}"
    echo "    /geo audit <url>      Full GEO + SEO audit"
    echo "    /geo quick <url>      60-second visibility snapshot"
    echo "    /geo citability <url> AI citation readiness score"
    echo "    /geo crawlers <url>   AI crawler access check"
    echo "    /geo llmstxt <url>    Analyze/generate llms.txt"
    echo "    /geo brands <url>     Brand mention scan"
    echo "    /geo platforms <url>  Platform-specific optimization"
    echo "    /geo schema <url>     Structured data analysis"
    echo "    /geo technical <url>  Technical SEO audit"
    echo "    /geo content <url>    Content quality & E-E-A-T"
    echo "    /geo report <url>     Client-ready GEO report"
    echo "    /geo report-pdf       Generate PDF report from audit data"
    echo ""
    echo "  Documentation: https://github.com/zubair-trabzada/geo-seo-claude"
    echo ""
}

main "$@"
