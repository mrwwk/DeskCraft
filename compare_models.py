"""compare_models.py — Compare multiple OSWorld model results in three summary tables.

Usage:
    python compare_models.py \
        results/ModelA/pyautogui/screenshot/ModelA \
        results/ModelB/pyautogui/screenshot/ModelB \
        [--levels L1 L2 L3] \
        [--csv-out comparison.csv] \
        [--no-plot]

Each positional argument is a result-root folder (same format expected by
stats_result_by_software_and_level.py).  The model name defaults to the last
path component but can be overridden with ``name=path`` syntax, e.g.:
    "GPT-4o=results/gpt4o/pyautogui/screenshot/gpt4o"

Output:
    Table 1  — rows=models, cols=software accuracy
    Table 2  — rows=models, cols=L1/L2/L3 accuracy
    Table 3  — rows=models, cols=software×level accuracy (e.g. gimp_L1, gimp_L2 …)
"""

import argparse
import csv
import io
import sys
from pathlib import Path

# ── reuse helpers from the existing sibling script ──────────────────────────
from stats_result_by_software_and_level import (
    ALL_LEVELS,
    INTERACTIVE_LEVEL,
    SOFTWARE_CATEGORIES,
    VALID_LEVELS,
    collect_stats,
    get_visible_levels,
)

# ── optional rich-table pretty-print ────────────────────────────────────────
try:
    from rich.console import Console
    from rich.table import Table as RichTable

    _RICH_AVAILABLE = True
except ImportError:
    _RICH_AVAILABLE = False


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

def parse_model_args(raw_args: list[str]) -> list[tuple[str, Path]]:
    """Return list of (model_name, resolved_path) pairs.

    Accepts either:
      - plain path  →  model name = last path component
      - "Name=path" →  model name = Name
    """
    models: list[tuple[str, Path]] = []
    for arg in raw_args:
        if "=" in arg and not Path(arg).exists():
            name, _, path_str = arg.partition("=")
            path = Path(path_str).expanduser().resolve()
        else:
            path = Path(arg).expanduser().resolve()
            name = path.name
        if not path.is_dir():
            print(f"[WARN] Result directory does not exist, skipping: {path}", file=sys.stderr)
            continue
        models.append((name, path))
    return models


def fmt(accuracy: float, count: int, *, show_count: bool = False) -> str:
    """Format an accuracy cell, optionally appending task count."""
    if count == 0:
        return "—"
    s = f"{accuracy:.1f}%"
    if show_count:
        s += f" ({count})"
    return s


# ────────────────────────────────────────────────────────────────────────────
# Build the three data matrices
# ────────────────────────────────────────────────────────────────────────────

def build_table1(
    model_summaries: list[tuple[str, dict]],
    software_cols: list[str],
    *,
    show_count: bool = False,
) -> tuple[list[str], list[list[str]]]:
    """Table 1: model × software accuracy."""
    headers = ["Model", "Overall"] + software_cols
    rows: list[list[str]] = []
    for model_name, summary in model_summaries:
        overall = summary["overall"]
        row = [model_name, fmt(overall["accuracy"], overall["count"], show_count=show_count)]
        for sw in software_cols:
            stats = summary["by_software"].get(sw, {"accuracy": 0.0, "count": 0})
            row.append(fmt(stats["accuracy"], stats["count"], show_count=show_count))
        rows.append(row)
    return headers, rows


def build_table2(
    model_summaries: list[tuple[str, dict]],
    level_cols: list[str],
    *,
    show_count: bool = False,
) -> tuple[list[str], list[list[str]]]:
    """Table 2: model × level accuracy."""
    headers = ["Model", "Overall"] + level_cols
    rows: list[list[str]] = []
    for model_name, summary in model_summaries:
        overall = summary["overall"]
        row = [model_name, fmt(overall["accuracy"], overall["count"], show_count=show_count)]
        for level in level_cols:
            stats = summary["by_level"].get(level, {"accuracy": 0.0, "count": 0})
            row.append(fmt(stats["accuracy"], stats["count"], show_count=show_count))
        rows.append(row)
    return headers, rows


def build_table3(
    model_summaries: list[tuple[str, dict]],
    software_cols: list[str],
    level_cols: list[str],
    *,
    show_count: bool = False,
) -> tuple[list[str], list[list[str]]]:
    """Table 3: model × (software × level) accuracy."""
    # Column order: sw_L1, sw_L2, sw_L3, … for each software
    col_pairs: list[tuple[str, str]] = [
        (sw, lvl) for sw in software_cols for lvl in level_cols
    ]
    headers = ["Model"] + [f"{sw}_{lvl}" for sw, lvl in col_pairs]
    rows: list[list[str]] = []
    for model_name, summary in model_summaries:
        row = [model_name]
        for sw, lvl in col_pairs:
            sw_level_data = summary.get("by_software_and_level", {}).get(sw, {})
            stats = sw_level_data.get(lvl, {"accuracy": 0.0, "count": 0})
            row.append(fmt(stats["accuracy"], stats["count"], show_count=show_count))
        rows.append(row)
    return headers, rows


# ────────────────────────────────────────────────────────────────────────────
# Rendering helpers
# ────────────────────────────────────────────────────────────────────────────

def _plain_table(title: str, headers: list[str], rows: list[list[str]]) -> str:
    """Render a plain-text aligned table."""
    all_rows = [headers] + rows
    col_widths = [max(len(str(r[c])) for r in all_rows) for c in range(len(headers))]
    sep = "  "

    lines: list[str] = [f"\n{'─' * 4} {title} {'─' * 4}"]
    header_line = sep.join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers))
    lines.append(header_line)
    lines.append("  ".join("─" * w for w in col_widths))
    for row in rows:
        lines.append(sep.join(str(v).ljust(col_widths[i]) for i, v in enumerate(row)))
    return "\n".join(lines)


def print_table(title: str, headers: list[str], rows: list[list[str]]) -> None:
    if _RICH_AVAILABLE:
        console = Console()
        rt = RichTable(title=title, show_lines=True)
        rt.add_column(headers[0], style="bold cyan", no_wrap=True)
        for h in headers[1:]:
            rt.add_column(h, justify="right")
        for row in rows:
            rt.add_row(*row)
        console.print(rt)
    else:
        print(_plain_table(title, headers, rows))


def save_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def render_comparison_plot(
    model_summaries: list[tuple[str, dict]],
    software_cols: list[str],
    level_cols: list[str],
    output_dir: Path,
) -> list[Path]:
    """Optional matplotlib visualisations for the comparison."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("[WARN] matplotlib not available — skipping plots.", file=sys.stderr)
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    model_names = [name for name, _ in model_summaries]
    n_models = len(model_names)
    x = np.arange(n_models)

    # ── Plot A: accuracy by software ─────────────────────────────────────────
    n_sw = len(software_cols)
    if n_sw > 0:
        fig, ax = plt.subplots(figsize=(max(10, n_models * 1.4 + 2), 6))
        width = 0.8 / max(n_sw, 1)
        cmap = plt.get_cmap("tab20")
        for i, sw in enumerate(software_cols):
            vals = [
                summary["by_software"].get(sw, {"accuracy": 0.0})["accuracy"]
                for _, summary in model_summaries
            ]
            offset = (i - (n_sw - 1) / 2) * width
            bars = ax.bar(x + offset, vals, width=width, label=sw, color=cmap(i / max(n_sw, 1)))
            ax.bar_label(bars, fmt="%.0f", padding=2, fontsize=7)
        ax.set_xticks(x, model_names, rotation=15, ha="right")
        ax.set_ylabel("Accuracy (%)")
        ax.set_ylim(0, 115)
        ax.set_title("Model comparison — accuracy by software")
        ax.legend(loc="upper right", fontsize=8, ncol=max(1, n_sw // 5))
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        fig.tight_layout()
        p = output_dir / "comparison_by_software.png"
        fig.savefig(p, dpi=180, bbox_inches="tight")
        plt.close(fig)
        saved.append(p)

    # ── Plot B: accuracy by level ─────────────────────────────────────────────
    n_lvl = len(level_cols)
    if n_lvl > 0:
        fig, ax = plt.subplots(figsize=(max(8, n_models * 1.2 + 2), 5))
        width = 0.8 / max(n_lvl, 1)
        level_colors = {"L1": "#4c78a8", "L2": "#f58518", "L3": "#54a24b", INTERACTIVE_LEVEL: "#b279a2", "UNKNOWN": "#9d755d"}
        for i, lvl in enumerate(level_cols):
            vals = [
                summary["by_level"].get(lvl, {"accuracy": 0.0})["accuracy"]
                for _, summary in model_summaries
            ]
            offset = (i - (n_lvl - 1) / 2) * width
            color = level_colors.get(lvl, "#aec7e8")
            bars = ax.bar(x + offset, vals, width=width, label=lvl, color=color)
            ax.bar_label(bars, fmt="%.0f", padding=2, fontsize=8)
        ax.set_xticks(x, model_names, rotation=15, ha="right")
        ax.set_ylabel("Accuracy (%)")
        ax.set_ylim(0, 115)
        ax.set_title("Model comparison — accuracy by level")
        ax.legend(loc="upper right", fontsize=9)
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        fig.tight_layout()
        p = output_dir / "comparison_by_level.png"
        fig.savefig(p, dpi=180, bbox_inches="tight")
        plt.close(fig)
        saved.append(p)

    # ── Plot C: heatmap models × software (overall accuracy) ─────────────────
    if n_sw > 0 and n_models > 1:
        data = np.array([
            [summary["by_software"].get(sw, {"accuracy": 0.0})["accuracy"] for sw in software_cols]
            for _, summary in model_summaries
        ])
        fig, ax = plt.subplots(figsize=(max(8, n_sw * 1.1), max(4, n_models * 0.7)))
        im = ax.imshow(data, vmin=0, vmax=100, cmap="YlGnBu", aspect="auto")
        ax.set_xticks(range(n_sw), software_cols, rotation=40, ha="right")
        ax.set_yticks(range(n_models), model_names)
        ax.set_title("Model × software accuracy heatmap")
        for r, (_, summary) in enumerate(model_summaries):
            for c, sw in enumerate(software_cols):
                stats = summary["by_software"].get(sw, {"accuracy": 0.0, "count": 0})
                txt = f"{stats['accuracy']:.0f}%\n(n={stats['count']})"
                color = "white" if stats["accuracy"] >= 55 else "black"
                ax.text(c, r, txt, ha="center", va="center", color=color, fontsize=7)
        fig.colorbar(im, ax=ax, fraction=0.03, pad=0.04, label="Accuracy (%)")
        fig.tight_layout()
        p = output_dir / "comparison_heatmap_software.png"
        fig.savefig(p, dpi=180, bbox_inches="tight")
        plt.close(fig)
        saved.append(p)

    # ── Plot D: overall accuracy bar ─────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(max(6, n_models * 1.3), 5))
    overall_vals = [summary["overall"]["accuracy"] for _, summary in model_summaries]
    bars = ax.bar(model_names, overall_vals, color="#1f77b4", width=0.55)
    ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=9)
    ax.set_ylabel("Accuracy (%)")
    ax.set_ylim(0, 115)
    ax.set_title("Overall accuracy comparison")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    plt.xticks(rotation=15, ha="right")
    fig.tight_layout()
    p = output_dir / "comparison_overall.png"
    fig.savefig(p, dpi=180, bbox_inches="tight")
    plt.close(fig)
    saved.append(p)

    return saved


# ────────────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compare multiple OSWorld model result folders and output three summary tables:\n"
            "  Table 1 — model × software accuracy\n"
            "  Table 2 — model × level (L1/L2/L3) accuracy\n"
            "  Table 3 — model × (software × level) accuracy\n\n"
            "Each positional arg is a result-root path.  Optionally prefix with 'Name=' to\n"
            "override the model name, e.g.:  \"GPT-4o=results/gpt4o/pyautogui/screenshot/gpt4o\""
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "result_roots",
        nargs="+",
        metavar="[NAME=]PATH",
        help="One or more result-root paths (or Name=path pairs).",
    )
    parser.add_argument(
        "--levels",
        nargs="+",
        default=list(VALID_LEVELS),
        metavar="LEVEL",
        help=f"Levels to include (default: {' '.join(VALID_LEVELS)}). "
             f"Use 'all' to include INTERACTIVE and UNKNOWN as well.",
    )
    parser.add_argument(
        "--software",
        nargs="+",
        default=list(SOFTWARE_CATEGORIES),
        metavar="SW",
        help="Software categories to include (default: all).",
    )
    parser.add_argument(
        "--show-count",
        action="store_true",
        help="Append task count in parentheses after each accuracy value.",
    )
    parser.add_argument(
        "--csv-out",
        metavar="PREFIX",
        help=(
            "Save tables as CSV files.  Three files are written:\n"
            "  <PREFIX>_table1_by_software.csv\n"
            "  <PREFIX>_table2_by_level.csv\n"
            "  <PREFIX>_table3_by_software_level.csv"
        ),
    )
    parser.add_argument(
        "--plot-out-dir",
        metavar="DIR",
        help="Directory to save comparison plots.  Defaults to './comparison_plots'.",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Disable plot generation.",
    )
    args = parser.parse_args()

    # ── resolve level list ───────────────────────────────────────────────────
    if len(args.levels) == 1 and args.levels[0].lower() == "all":
        level_cols = list(ALL_LEVELS)
    else:
        level_cols = [lvl.upper() for lvl in args.levels]

    software_cols = args.software

    # ── load summaries ───────────────────────────────────────────────────────
    models = parse_model_args(args.result_roots)
    if not models:
        raise SystemExit("No valid result directories provided.")

    print(f"Loading {len(models)} model(s) …", file=sys.stderr)
    model_summaries: list[tuple[str, dict]] = []
    for model_name, result_root in models:
        print(f"  {model_name}  ←  {result_root}", file=sys.stderr)
        summary = collect_stats(result_root)
        model_summaries.append((model_name, summary))

    # ── build tables ─────────────────────────────────────────────────────────
    show_count = args.show_count
    h1, r1 = build_table1(model_summaries, software_cols, show_count=show_count)
    h2, r2 = build_table2(model_summaries, level_cols, show_count=show_count)
    h3, r3 = build_table3(model_summaries, software_cols, level_cols, show_count=show_count)

    # ── print ─────────────────────────────────────────────────────────────────
    print_table("Table 1 — Accuracy by Software", h1, r1)
    print()
    print_table("Table 2 — Accuracy by Level", h2, r2)
    print()
    print_table("Table 3 — Accuracy by Software × Level", h3, r3)

    # ── CSV export ────────────────────────────────────────────────────────────
    if args.csv_out:
        prefix = args.csv_out
        p1 = Path(f"{prefix}_table1_by_software.csv")
        p2 = Path(f"{prefix}_table2_by_level.csv")
        p3 = Path(f"{prefix}_table3_by_software_level.csv")
        save_csv(p1, h1, r1)
        save_csv(p2, h2, r2)
        save_csv(p3, h3, r3)
        print(f"\nCSV saved:\n  {p1}\n  {p2}\n  {p3}", file=sys.stderr)

    # ── plots ─────────────────────────────────────────────────────────────────
    if not args.no_plot:
        plot_dir = Path(args.plot_out_dir) if args.plot_out_dir else Path("comparison_plots")
        saved = render_comparison_plot(model_summaries, software_cols, level_cols, plot_dir)
        if saved:
            print("\nPlots saved:", file=sys.stderr)
            for p in saved:
                print(f"  {p}", file=sys.stderr)


if __name__ == "__main__":
    main()
