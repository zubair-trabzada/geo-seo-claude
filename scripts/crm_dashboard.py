#!/usr/bin/env python3
"""
GEO-SEO CRM Dashboard — CLI
Visualizza il CRM dei prospect con rich.

Usage:
    python crm_dashboard.py                  # Vista principale
    python crm_dashboard.py --prospect PRO-001   # Dettaglio singolo prospect
    python crm_dashboard.py --refresh           # Aggiorna + mostra
"""

import json
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.columns import Columns
    from rich.text import Text
    from rich.rule import Rule
    from rich.layout import Layout
    from rich.align import Align
    from rich import box
    from rich.progress import Progress, BarColumn, TextColumn
    from rich.padding import Padding
    from rich.style import Style
    from rich.markup import escape
except ImportError:
    print("ERROR: rich is required. Run: pip install rich")
    sys.exit(1)

# ── Paths ─────────────────────────────────────────────────────────────
CRM_PATH = Path.home() / ".geo-prospects" / "prospects.json"
AUDITS_DIR = Path.home() / ".geo-prospects" / "audits"
PROPOSALS_DIR = Path.home() / ".geo-prospects" / "proposals"

console = Console()

# ── Color helpers ──────────────────────────────────────────────────────
STATUS_STYLE = {
    "lead":     ("⬜", "dim white",       "grey50"),
    "audit":    ("🔍", "bold yellow",     "yellow"),
    "proposal": ("📄", "bold cyan",       "cyan"),
    "active":   ("✅", "bold green",      "green"),
    "churned":  ("❌", "dim red",         "red"),
    "lost":     ("💀", "dim red",         "red"),
}

def score_style(score: int) -> tuple[str, str]:
    """Returns (color, label) based on GEO score."""
    if score >= 80:
        return "bold green",  "GOOD"
    elif score >= 60:
        return "bold blue",   "MODERATE"
    elif score >= 40:
        return "bold yellow",  "POOR"
    else:
        return "bold red",    "CRITICAL"

def score_bar(score: int, width: int = 20) -> Text:
    """Renders a colored progress bar for a score."""
    filled = round((score / 100) * width)
    empty = width - filled
    color, _ = score_style(score)
    bar = Text()
    bar.append("█" * filled, style=color)
    bar.append("░" * empty, style="grey30")
    bar.append(f" {score}/100", style=color)
    return bar

def format_eur(value: int | None) -> str:
    if not value:
        return "—"
    return f"€{value:,.0f}".replace(",", ".")


# ── Load CRM ───────────────────────────────────────────────────────────
def load_prospects() -> list[dict]:
    if not CRM_PATH.exists():
        console.print(f"[red]CRM file not found:[/red] {CRM_PATH}")
        return []
    with open(CRM_PATH) as f:
        return json.load(f)


# ── Views ──────────────────────────────────────────────────────────────
def view_summary(prospects: list[dict]):
    """KPI summary cards at top."""
    total = len(prospects)
    active = sum(1 for p in prospects if p.get("status") == "active")
    pipeline = sum(p.get("monthly_value", 0) for p in prospects if p.get("status") == "proposal")
    mrr = sum(p.get("monthly_value", 0) for p in prospects if p.get("status") == "active")
    avg_score = round(sum(p.get("geo_score", 0) for p in prospects) / total) if total else 0

    cards = [
        Panel(
            Align.center(
                Text.from_markup(
                    f"[bold white]{total}[/bold white]\n[dim]Total Prospects[/dim]"
                )
            ),
            border_style="bright_blue",
            padding=(1, 3),
        ),
        Panel(
            Align.center(
                Text.from_markup(
                    f"[bold green]{active}[/bold green]\n[dim]Active Clients[/dim]"
                )
            ),
            border_style="green",
            padding=(1, 3),
        ),
        Panel(
            Align.center(
                Text.from_markup(
                    f"[bold cyan]{format_eur(mrr)}[/bold cyan]\n[dim]MRR[/dim]"
                )
            ),
            border_style="cyan",
            padding=(1, 3),
        ),
        Panel(
            Align.center(
                Text.from_markup(
                    f"[bold yellow]{format_eur(pipeline)}[/bold yellow]\n[dim]Pipeline (proposals)[/dim]"
                )
            ),
            border_style="yellow",
            padding=(1, 3),
        ),
        Panel(
            Align.center(
                Text.from_markup(
                    f"[bold]{avg_score}[/bold][dim]/100[/dim]\n[dim]Avg GEO Score[/dim]"
                )
            ),
            border_style="magenta",
            padding=(1, 3),
        ),
    ]
    console.print(Columns(cards, equal=True, expand=True))


def view_prospect_table(prospects: list[dict]):
    """Main prospects table."""
    table = Table(
        title=None,
        box=box.ROUNDED,
        border_style="bright_blue",
        header_style="bold bright_white on grey23",
        show_lines=False,
        expand=True,
        padding=(0, 1),
    )

    table.add_column("ID",         style="dim", width=9)
    table.add_column("Company",    style="bold white", min_width=16)
    table.add_column("Domain",     style="cyan", min_width=18)
    table.add_column("Status",     justify="center", min_width=12)
    table.add_column("GEO Score",  justify="left", min_width=26)
    table.add_column("Audit",      justify="center", min_width=12)
    table.add_column("MRR",        justify="right", min_width=10)
    table.add_column("Proposal",   justify="center", min_width=10)

    for p in sorted(prospects, key=lambda x: x.get("geo_score", 0)):
        pid     = p.get("id", "—")
        company = p.get("company", "—")
        domain  = p.get("domain", "—")
        status  = p.get("status", "lead")
        score   = p.get("geo_score", 0)
        audit   = p.get("audit_date", "—")
        mrr     = format_eur(p.get("monthly_value"))
        has_proposal = "✓" if p.get("proposal_file") else "—"

        icon, status_style, _ = STATUS_STYLE.get(status, ("?", "white", "white"))
        status_text = Text(f"{icon} {status.upper()}", style=status_style)

        table.add_row(
            pid,
            company,
            domain,
            status_text,
            score_bar(score),
            audit,
            mrr,
            has_proposal,
        )

    console.print(table)


def view_prospect_detail(prospects: list[dict], prospect_id: str):
    """Detailed view of a single prospect."""
    p = next((x for x in prospects if x.get("id") == prospect_id), None)
    if not p:
        console.print(f"[red]Prospect not found:[/red] {prospect_id}")
        return

    score = p.get("geo_score", 0)
    color, label = score_style(score)

    # Header
    console.print(Rule(f"[bold]{p['company']}[/bold] — {p['domain']}", style="bright_blue"))
    console.print()

    # Score + info side by side
    score_panel = Panel(
        Align.center(
            Text.from_markup(
                f"\n[{color}]{score}[/{color}]\n[dim]/100[/dim]\n\n[{color}]{label}[/{color}]\n"
            )
        ),
        title="GEO Score",
        border_style=color.replace("bold ", ""),
        width=20,
    )

    info_lines = [
        f"[dim]ID:[/dim]          {p.get('id', '—')}",
        f"[dim]Status:[/dim]      {p.get('status', '—').upper()}",
        f"[dim]Industry:[/dim]    {p.get('industry', '—')}",
        f"[dim]Country:[/dim]     {p.get('country', '—')}",
        f"[dim]Audit Date:[/dim]  {p.get('audit_date', '—')}",
        f"[dim]MRR:[/dim]         {format_eur(p.get('monthly_value'))}",
        f"[dim]Contract:[/dim]    {p.get('contract_months', '—')} months",
    ]
    if p.get("contact_name"):
        info_lines.append(f"[dim]Contact:[/dim]     {p['contact_name']}")
    if p.get("contact_email"):
        info_lines.append(f"[dim]Email:[/dim]       {p['contact_email']}")

    info_panel = Panel(
        "\n".join(info_lines),
        title="Details",
        border_style="bright_blue",
    )

    console.print(Columns([score_panel, info_panel], expand=False))
    console.print()

    # Files
    files = []
    if p.get("audit_file"):
        audit_path = Path(p["audit_file"].replace("~", str(Path.home())))
        exists = "✓" if audit_path.exists() else "✗"
        files.append(f"  {exists} [cyan]Audit:[/cyan]    {p['audit_file']}")
    if p.get("proposal_file"):
        prop_path = Path(p["proposal_file"].replace("~", str(Path.home())))
        exists = "✓" if prop_path.exists() else "✗"
        files.append(f"  {exists} [yellow]Proposal:[/yellow] {p['proposal_file']}")
    if files:
        console.print(Panel("\n".join(files), title="Files", border_style="dim"))
        console.print()

    # Notes
    notes = p.get("notes", [])
    if notes:
        note_text = ""
        for note in notes:
            date = note.get("date", "")[:10]
            text = escape(note.get("text", ""))
            note_text += f"[dim]{date}[/dim]  {text}\n\n"
        console.print(Panel(note_text.rstrip(), title="Notes", border_style="dim"))


def view_pipeline(prospects: list[dict]):
    """Show pipeline by status."""
    statuses = ["lead", "audit", "proposal", "active", "churned", "lost"]
    console.print()
    console.print(Rule("[bold]Pipeline by Status[/bold]", style="bright_blue"))
    console.print()

    for status in statuses:
        group = [p for p in prospects if p.get("status") == status]
        if not group:
            continue
        icon, style, _ = STATUS_STYLE.get(status, ("?", "white", "white"))
        total_mrr = sum(p.get("monthly_value", 0) for p in group)
        label = f"{icon} [bold]{status.upper()}[/bold] ({len(group)})  {format_eur(total_mrr)}/mo"
        console.print(f"  {label}", style=style)
        for p in group:
            score = p.get("geo_score", 0)
            color, _ = score_style(score)
            console.print(
                f"    [dim]·[/dim] {p.get('company', '—'):<25} [{color}]{score:>3}/100[/{color}]  [dim]{p.get('domain', '—')}[/dim]"
            )
        console.print()


# ── Main ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="GEO-SEO CRM Dashboard")
    parser.add_argument("--prospect", "-p", help="Show detail for a prospect ID")
    parser.add_argument("--pipeline", action="store_true", help="Show pipeline view")
    args = parser.parse_args()

    prospects = load_prospects()
    if not prospects:
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    console.print()
    console.print(
        Panel.fit(
            f"[bold bright_white]GEO-SEO CRM[/bold bright_white]  [dim]—  {now}[/dim]",
            border_style="bright_blue",
            padding=(0, 2),
        )
    )
    console.print()

    if args.prospect:
        view_prospect_detail(prospects, args.prospect)
    elif args.pipeline:
        view_pipeline(prospects)
    else:
        view_summary(prospects)
        console.print()
        view_prospect_table(prospects)
        console.print()
        view_pipeline(prospects)

    console.print(
        f"[dim]CRM: {CRM_PATH}   |   /geo audit <domain> to add prospects[/dim]\n"
    )


if __name__ == "__main__":
    main()
