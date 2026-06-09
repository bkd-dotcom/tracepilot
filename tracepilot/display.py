"""Display utilities for TracePilot using the Rich library.

Renders confidence tables, routing decisions, run results,
and audit summaries with color-coded metrics and emoji indicators.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()


def _confidence_style(confidence: float) -> tuple[str, str]:
    """Return (emoji, rich color) for a confidence value."""
    if confidence >= 0.7:
        return "🟢", "green"
    if confidence >= 0.3:
        return "🟡", "yellow"
    return "🔴", "red"


def print_confidence_table(rows: list[dict]) -> None:
    """Print a Rich table summarising per-tool confidence metrics.

    Each dict in *rows* must contain keys:
        category, tool, runs, success_rate, confidence,
        avg_cost, avg_latency, avg_recovery
    """
    if not rows:
        console.print(
            "[dim italic]No data yet. Run some queries first.[/dim italic]"
        )
        return

    table = Table(
        title="📊 Confidence Table",
        show_lines=True,
        header_style="bold cyan",
    )
    table.add_column("Category", style="bold")
    table.add_column("Tool")
    table.add_column("Runs", justify="right")
    table.add_column("Success Rate", justify="right")
    table.add_column("Confidence", justify="right")
    table.add_column("Avg Cost", justify="right")
    table.add_column("Avg Latency", justify="right")
    table.add_column("Avg Recovery", justify="right")

    for row in rows:
        emoji, color = _confidence_style(row["confidence"])
        conf_text = Text(f"{emoji} {row['confidence']:.2f}", style=color)

        table.add_row(
            row["category"],
            row["tool"],
            str(row["runs"]),
            f"{row['success_rate']:.0%}",
            conf_text,
            f"${row['avg_cost']:.3f}",
            f"{row['avg_latency']:.1f}s",
            f"${row['avg_recovery']:.3f}",
        )

    console.print(table)


def print_routing_decision(
    category: str,
    selected_tool: str,
    confidence: float,
    mode: str,
    all_options: list[dict],
) -> None:
    """Print the routing decision with explainability.

    *all_options* is a list of dicts with keys:
        tool, confidence, success_rate, avg_cost, avg_recovery
    """
    emoji, color = _confidence_style(confidence)

    lines = Text()
    lines.append("Category:  ", style="bold")
    lines.append(f"{category}\n")
    lines.append("Selected:  ", style="bold")
    lines.append(f"{selected_tool}", style=f"bold {color}")
    lines.append(f"  (Confidence: {confidence:.2f})\n")
    lines.append("Mode:      ", style="bold")
    lines.append(f"{mode}\n\n")
    lines.append("Why this tool?\n", style="bold underline")

    for opt in all_options:
        is_selected = opt["tool"] == selected_tool
        marker = "✅" if is_selected else "❌"
        opt_emoji, opt_color = _confidence_style(opt["confidence"])
        style = f"bold {opt_color}" if is_selected else f"dim {opt_color}"

        lines.append(f" {marker} ", style=style)
        lines.append(f"{opt['tool']}", style=style)
        lines.append(f" — Confidence: {opt['confidence']:.2f}\n", style=style)
        lines.append(
            f"    Success: {opt['success_rate']:.0%}"
            f" | Avg Cost: ${opt['avg_cost']:.2f}"
            f" | Recovery: ${opt.get('avg_recovery', 0):.2f}\n",
            style="dim" if not is_selected else "",
        )

    panel = Panel(
        lines,
        title="[bold]Routing Decision[/bold]",
        border_style="blue",
        expand=False,
    )
    console.print(panel)


def print_run_result(
    query: str,
    tool_used: str,
    success: bool,
    result: str,
    latency: float,
    cost: float,
    recovery_cost: float,
) -> None:
    """Print the result of a single tool run with metrics."""
    status_emoji = "✅" if success else "❌"
    status_label = "Success" if success else "Failure"
    status_color = "green" if success else "red"

    lines = Text()
    lines.append("Query:    ", style="bold")
    lines.append(f'"{query}"\n')
    lines.append("Tool:     ", style="bold")
    lines.append(f"{tool_used}\n")
    lines.append("Status:   ", style="bold")
    lines.append(f"{status_emoji} {status_label}\n", style=status_color)
    lines.append("Result:   ", style="bold")
    lines.append(f"{result}\n", style="dim")
    lines.append("Latency:  ", style="bold")
    lines.append(f"{latency:.1f}s\n")
    lines.append("Cost:     ", style="bold")
    lines.append(f"${cost:.2f}\n")
    lines.append("Recovery: ", style="bold")
    lines.append(f"${recovery_cost:.2f}\n")

    panel = Panel(
        lines,
        title="[bold]Run Result[/bold]",
        border_style="green" if success else "red",
        expand=False,
    )
    console.print(panel)


def print_audit_summary(
    before: list[dict],
    after: list[dict],
) -> None:
    """Print a before/after comparison of confidence changes.

    Each dict in *before* / *after* must contain keys:
        category, tool, confidence, success_rate
    """
    table = Table(
        title="🔍 Audit Summary — Confidence Changes",
        show_lines=True,
        header_style="bold magenta",
    )
    table.add_column("Category", style="bold")
    table.add_column("Tool")
    table.add_column("Before", justify="right")
    table.add_column("After", justify="right")
    table.add_column("Δ Confidence", justify="right")
    table.add_column("Δ Success Rate", justify="right")

    # Index the *after* list for fast lookup
    after_map: dict[tuple[str, str], dict] = {
        (r["category"], r["tool"]): r for r in after
    }

    for b in before:
        key = (b["category"], b["tool"])
        a = after_map.get(key)
        if a is None:
            continue

        delta_conf = a["confidence"] - b["confidence"]
        delta_sr = a["success_rate"] - b["success_rate"]

        arrow_conf = "↑" if delta_conf > 0 else ("↓" if delta_conf < 0 else "─")
        arrow_sr = "↑" if delta_sr > 0 else ("↓" if delta_sr < 0 else "─")

        delta_color = "green" if delta_conf >= 0 else "red"
        sr_color = "green" if delta_sr >= 0 else "red"

        b_emoji, b_color = _confidence_style(b["confidence"])
        a_emoji, a_color = _confidence_style(a["confidence"])

        table.add_row(
            b["category"],
            b["tool"],
            Text(f"{b_emoji} {b['confidence']:.2f}", style=b_color),
            Text(f"{a_emoji} {a['confidence']:.2f}", style=a_color),
            Text(f"{arrow_conf} {delta_conf:+.2f}", style=delta_color),
            Text(f"{arrow_sr} {delta_sr:+.0%}", style=sr_color),
        )

    console.print(table)
