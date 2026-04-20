import argparse
import ast
import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


VALID_LEVELS = ("L1", "L2", "L3")
INTERACTIVE_LEVEL = "INTERACTIVE"
ALL_LEVELS = VALID_LEVELS + (INTERACTIVE_LEVEL, "UNKNOWN")
SOFTWARE_CATEGORIES = (
    "multi_app",
    "calc",
    "impr",
    "writ",
    "audacity",
    "blender",
    "chrome",
    "gimp",
    "inkscape",
    "kdenlive",
    "os",
    "ui_gen",
    "vscode",
)
SOFTWARE_ALIASES = {
    "multi_app": "multi_app",
    "multi_apps": "multi_app",
    "mutil_app": "multi_app",
    "mutil_apps": "multi_app",
    "libreoffice_suite": "multi_app",
    "libreoffice_multi_njc": "multi_app",
    "multiapp": "multi_app",
    "calc": "calc",
    "libreoffice_calc": "calc",
    "impr": "impr",
    "impress": "impr",
    "libreoffice_impress": "impr",
    "writ": "writ",
    "writer": "writ",
    "libreoffice_writer": "writ",
    "audacity": "audacity",
    "blender": "blender",
    "chrome": "chrome",
    "google_chrome": "chrome",
    "gimp": "gimp",
    "inkscape": "inkscape",
    "kdenlive": "kdenlive",
    "os": "os",
    "basic_os": "os",
    "ui_gen": "ui_gen",
    "vscode": "vscode",
    "vs_code": "vscode",
    "code": "vscode",
}
PLOT_COLORS = {
    "overall": "#1f77b4",
    "level": "#ff7f0e",
    "count_l1": "#4c78a8",
    "count_l2": "#f58518",
    "count_l3": "#54a24b",
    "count_interactive": "#b279a2",
    "count_unknown": "#9d755d",
    "score_hist": "#72b7b2",
}


def normalize_score(score: float) -> float:
    return 1.0 if score >= 0.8 else 0.0


def parse_result(result_path: Path) -> float:
    raw = result_path.read_text(encoding="utf-8").strip()
    if not raw:
        return 0.0

    try:
        return normalize_score(float(raw))
    except ValueError:
        pass

    lowered = raw.lower()
    if lowered in {"true", "false"}:
        return 1.0 if lowered == "true" else 0.0

    try:
        parsed = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return 1.0 if raw else 0.0

    if isinstance(parsed, bool):
        return 1.0 if parsed else 0.0

    if isinstance(parsed, (int, float)):
        return normalize_score(float(parsed))

    return 1.0 if parsed else 0.0


def normalize_software_name(name: str) -> str | None:
    lowered = name.lower()
    exact_match = SOFTWARE_ALIASES.get(lowered)
    if exact_match:
        return exact_match

    matches: list[tuple[int, int, str]] = []
    for alias, normalized_name in SOFTWARE_ALIASES.items():
        pattern = rf"(^|[^a-z0-9]){re.escape(alias)}(?=$|[^a-z0-9])"
        match = re.search(pattern, lowered)
        if match:
            matches.append((match.start(), -len(alias), normalized_name))

    if matches:
        matches.sort()
        return matches[0][2]

    return None


def extract_software_category(software_dir_name: str, task_dir_name: str) -> str | None:
    normalized_dir_name = normalize_software_name(software_dir_name)
    if normalized_dir_name in SOFTWARE_CATEGORIES:
        return normalized_dir_name

    task_name = task_dir_name.lower()
    matches: list[tuple[int, str]] = []
    for alias, normalized_name in SOFTWARE_ALIASES.items():
        pattern = rf"(^|[^a-z0-9]){re.escape(alias)}(?=$|[^a-z0-9])"
        match = re.search(pattern, task_name)
        if match:
            matches.append((match.start(), normalized_name))

    if matches:
        matches.sort(key=lambda item: item[0])
        return matches[0][1]

    return None


def extract_level(task_dir_name: str) -> str:
    lowered = task_dir_name.lower()
    if "interactive" in lowered:
        return INTERACTIVE_LEVEL

    match = re.search(r"(^|[_-])(L[123])(?=$|[_-])", task_dir_name)
    if match:
        return match.group(2)

    for level in VALID_LEVELS:
        if task_dir_name.endswith(f"_{level}") or task_dir_name.startswith(f"{level}_"):
            return level
    return "UNKNOWN"


def iter_task_dirs(result_root: Path):
    for software_dir in sorted(result_root.iterdir()):
        if not software_dir.is_dir():
            continue

        direct_children = sorted(child for child in software_dir.iterdir() if child.is_dir())
        has_direct_results = any((child / "result.txt").is_file() for child in direct_children)
        if has_direct_results:
            for task_dir in direct_children:
                yield software_dir, task_dir
            continue

        for container_dir in direct_children:
            nested_children = sorted(child for child in container_dir.iterdir() if child.is_dir())
            for task_dir in nested_children:
                yield container_dir, task_dir


def compute_summary(values: list[float]) -> dict:
    total = len(values)
    success = sum(values)
    accuracy = (success / total * 100.0) if total else 0.0
    return {
        "count": total,
        "success": success,
        "accuracy": accuracy,
    }


def collect_stats(result_root: Path) -> dict:
    software_stats: dict[str, list[float]] = {}
    software_level_stats: dict[str, dict[str, list[float]]] = {}
    level_stats: dict[str, list[float]] = {level: [] for level in ALL_LEVELS}
    overall_results: list[float] = []
    detailed_rows: list[dict] = []

    for source_dir, task_dir in iter_task_dirs(result_root):
        result_path = task_dir / "result.txt"
        if not result_path.is_file():
            continue

        score = parse_result(result_path)
        software = extract_software_category(source_dir.name, task_dir.name)
        if software is None:
            continue
        level = extract_level(task_dir.name)

        software_stats.setdefault(software, []).append(score)
        software_level_stats.setdefault(
            software,
            {level_name: [] for level_name in ALL_LEVELS},
        )[level].append(score)
        level_stats[level].append(score)
        overall_results.append(score)
        detailed_rows.append(
            {
                "software": software,
                "source_dir": source_dir.name,
                "task": task_dir.name,
                "level": level,
                "score": score,
            }
        )

    return {
        "root": str(result_root),
        "overall": compute_summary(overall_results),
        "by_software": {
            software: compute_summary(scores)
            for software, scores in sorted(software_stats.items())
        },
        "by_software_and_level": {
            software: {
                level: compute_summary(level_scores[level])
                for level in ALL_LEVELS
            }
            for software, level_scores in sorted(software_level_stats.items())
        },
        "by_level": {
            level: compute_summary(level_stats[level])
            for level in ALL_LEVELS
        },
        "details": detailed_rows,
    }


def print_summary(summary: dict) -> None:
    print(f"Result root: {summary['root']}")
    print()

    overall = summary["overall"]
    print(
        "Overall: "
        f"count={overall['count']} success={overall['success']:.1f} "
        f"accuracy={overall['accuracy']:.2f}%"
    )
    print()

    print("By software:")
    for software, stats in summary["by_software"].items():
        print(
            f"  {software}: count={stats['count']} success={stats['success']:.1f} "
            f"accuracy={stats['accuracy']:.2f}%"
        )
        for level, level_stats in summary["by_software_and_level"][software].items():
            print(
                f"    {level}: count={level_stats['count']} "
                f"success={level_stats['success']:.1f} "
                f"accuracy={level_stats['accuracy']:.2f}%"
            )
    print()

    print("By level:")
    for level, stats in summary["by_level"].items():
        print(
            f"  {level}: count={stats['count']} success={stats['success']:.1f} "
            f"accuracy={stats['accuracy']:.2f}%"
        )


def get_visible_levels(summary: dict) -> list[str]:
    levels = [level for level in VALID_LEVELS if summary["by_level"][level]["count"] > 0]
    if summary["by_level"][INTERACTIVE_LEVEL]["count"] > 0:
        levels.append(INTERACTIVE_LEVEL)
    if summary["by_level"]["UNKNOWN"]["count"] > 0:
        levels.append("UNKNOWN")
    return levels or list(VALID_LEVELS)


def add_bar_labels(ax: plt.Axes, values: list[float]) -> None:
    for index, value in enumerate(values):
        ax.text(
            value + 1.0,
            index,
            f"{value:.1f}%",
            va="center",
            ha="left",
            fontsize=9,
        )


def add_vertical_bar_labels(ax: plt.Axes, values: list[float]) -> None:
    y_max = ax.get_ylim()[1]
    offset = max(y_max * 0.015, 0.3)
    for index, value in enumerate(values):
        ax.text(
            index,
            value + offset,
            f"{value:.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )


def build_heatmap(summary: dict, levels: list[str]) -> tuple[list[str], list[list[float]]]:
    software_names = list(summary["by_software_and_level"].keys())
    heatmap_rows: list[list[float]] = []

    for software in software_names:
        heatmap_rows.append(
            [summary["by_software_and_level"][software][level]["accuracy"] for level in levels]
        )

    return software_names, heatmap_rows


def get_level_counts(summary: dict, levels: list[str]) -> dict[str, list[int]]:
    counts_by_level: dict[str, list[int]] = {level: [] for level in levels}
    for software in summary["by_software_and_level"]:
        for level in levels:
            counts_by_level[level].append(summary["by_software_and_level"][software][level]["count"])
    return counts_by_level


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_") or "unknown"


def render_dashboard(summary: dict, output_dir: Path, levels: list[str]) -> Path:
    software_stats = sorted(
        summary["by_software"].items(),
        key=lambda item: item[1]["accuracy"],
        reverse=True,
    )
    software_names = [name for name, _ in software_stats]
    software_accuracies = [stats["accuracy"] for _, stats in software_stats]
    level_accuracies = [summary["by_level"][level]["accuracy"] for level in levels]
    heatmap_names, heatmap_values = build_heatmap(summary, levels)

    figure_height = max(8, len(software_names) * 0.6 + 3)
    fig = plt.figure(figsize=(16, figure_height))
    grid = fig.add_gridspec(2, 2, width_ratios=(1.15, 1.0), height_ratios=(1.0, 1.25))

    ax_software = fig.add_subplot(grid[:, 0])
    ax_level = fig.add_subplot(grid[0, 1])
    ax_heatmap = fig.add_subplot(grid[1, 1])

    ax_software.barh(software_names, software_accuracies, color=PLOT_COLORS["overall"])
    ax_software.invert_yaxis()
    ax_software.set_xlim(0, 110)
    ax_software.set_xlabel("Accuracy (%)")
    ax_software.set_title("Accuracy by software")
    ax_software.grid(axis="x", linestyle="--", alpha=0.3)
    add_bar_labels(ax_software, software_accuracies)

    ax_level.bar(levels, level_accuracies, color=PLOT_COLORS["level"], width=0.55)
    ax_level.set_ylim(0, 110)
    ax_level.set_ylabel("Accuracy (%)")
    ax_level.set_title("Accuracy by level")
    ax_level.grid(axis="y", linestyle="--", alpha=0.3)
    for index, value in enumerate(level_accuracies):
        ax_level.text(index, value + 2.0, f"{value:.1f}%", ha="center", va="bottom", fontsize=9)

    heatmap = ax_heatmap.imshow(heatmap_values, vmin=0, vmax=100, cmap="YlGnBu", aspect="auto")
    ax_heatmap.set_xticks(range(len(levels)), levels)
    ax_heatmap.set_yticks(range(len(heatmap_names)), heatmap_names)
    ax_heatmap.set_title("Software vs. level accuracy")
    for row_index, software in enumerate(heatmap_names):
        for col_index, level in enumerate(levels):
            stats = summary["by_software_and_level"][software][level]
            display = f"{stats['accuracy']:.1f}%\n(n={stats['count']})"
            text_color = "white" if stats["accuracy"] >= 55 else "black"
            ax_heatmap.text(col_index, row_index, display, ha="center", va="center", color=text_color, fontsize=8)

    colorbar = fig.colorbar(heatmap, ax=ax_heatmap, fraction=0.046, pad=0.04)
    colorbar.set_label("Accuracy (%)")

    overall = summary["overall"]
    fig.suptitle(
        "OSWorld result summary\n"
        f"Overall accuracy {overall['accuracy']:.2f}% | success {overall['success']:.1f} / {overall['count']}",
        fontsize=16,
        y=0.98,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))

    dashboard_path = output_dir / "summary_dashboard.png"
    fig.savefig(dashboard_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return dashboard_path


def render_task_count_by_software(summary: dict, output_dir: Path, levels: list[str]) -> Path:
    software_names = list(summary["by_software_and_level"].keys())
    counts_by_level = get_level_counts(summary, levels)

    fig, ax = plt.subplots(figsize=(max(10, len(software_names) * 1.2), 6.5))
    x_positions = list(range(len(software_names)))
    width = 0.75 / max(len(levels), 1)
    offsets = [index - (len(levels) - 1) / 2 for index in range(len(levels))]

    for index, level in enumerate(levels):
        values = counts_by_level[level]
        shifted = [x + offsets[index] * width for x in x_positions]
        color_key = {
            "L1": "count_l1",
            "L2": "count_l2",
            "L3": "count_l3",
            INTERACTIVE_LEVEL: "count_interactive",
            "UNKNOWN": "count_unknown",
        }[level]
        ax.bar(shifted, values, width=width, label=level, color=PLOT_COLORS[color_key])

    ax.set_xticks(x_positions, software_names, rotation=20, ha="right")
    ax.set_ylabel("Task count")
    ax.set_title("Task counts by software and level")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.legend(title="Level")

    for container in ax.containers:
        ax.bar_label(container, fmt="%.0f", padding=3, fontsize=8)

    fig.tight_layout()
    plot_path = output_dir / "task_count_by_software_and_level.png"
    fig.savefig(plot_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return plot_path


def render_task_count_by_level(summary: dict, output_dir: Path, levels: list[str]) -> Path:
    counts = [summary["by_level"][level]["count"] for level in levels]
    level_color_keys = {
        "L1": "count_l1",
        "L2": "count_l2",
        "L3": "count_l3",
        INTERACTIVE_LEVEL: "count_interactive",
        "UNKNOWN": "count_unknown",
    }
    colors = [PLOT_COLORS[level_color_keys[level]] for level in levels]

    # Filter out zero-count levels
    non_zero = [(lvl, cnt, clr) for lvl, cnt, clr in zip(levels, counts, colors) if cnt > 0]
    if not non_zero:
        non_zero = list(zip(levels, counts, colors))
    labels, sizes, pie_colors = zip(*non_zero)

    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=pie_colors,
        autopct=lambda pct: f"{pct:.1f}%\n({int(round(pct / 100 * sum(sizes)))})",
        startangle=90,
        pctdistance=0.75,
        wedgeprops={"linewidth": 1.0, "edgecolor": "white"},
    )
    for autotext in autotexts:
        autotext.set_fontsize(9)
    ax.set_title(f"Overall task counts by level  (total={sum(sizes)})", fontsize=13)

    fig.tight_layout()
    plot_path = output_dir / "task_count_by_level.png"
    fig.savefig(plot_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return plot_path


def render_task_count_by_software_pie(summary: dict, output_dir: Path) -> Path:
    software_counts = [
        (software, stats["count"])
        for software, stats in summary["by_software"].items()
        if stats["count"] > 0
    ]
    software_counts.sort(key=lambda x: x[1], reverse=True)
    labels, sizes = zip(*software_counts) if software_counts else ([], [])

    cmap = plt.get_cmap("tab20")
    colors = [cmap(i / max(len(labels), 1)) for i in range(len(labels))]

    fig, ax = plt.subplots(figsize=(9, 7))
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct=lambda pct: f"{pct:.1f}%\n({int(round(pct / 100 * sum(sizes)))})",
        startangle=90,
        pctdistance=0.78,
        wedgeprops={"linewidth": 1.0, "edgecolor": "white"},
    )
    for autotext in autotexts:
        autotext.set_fontsize(8)
    ax.set_title(f"Task counts by software  (total={sum(sizes)})", fontsize=13)

    fig.tight_layout()
    plot_path = output_dir / "task_count_by_software_pie.png"
    fig.savefig(plot_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return plot_path


def render_score_distribution(summary: dict, output_dir: Path) -> Path:
    scores = [row["score"] for row in summary["details"]]
    if not scores:
        raise ValueError("No scores available for plotting.")

    fig, ax = plt.subplots(figsize=(9, 5.5))
    unique_scores = sorted(set(scores))
    if all(score in {0.0, 1.0} for score in unique_scores):
        bins = [-0.5, 0.5, 1.5]
        ax.hist(scores, bins=bins, color=PLOT_COLORS["score_hist"], edgecolor="white", rwidth=0.7)
        ax.set_xticks([0.0, 1.0], ["Fail (0)", "Pass (1)"])
    else:
        bin_count = min(20, max(5, len(unique_scores)))
        ax.hist(scores, bins=bin_count, color=PLOT_COLORS["score_hist"], edgecolor="white")
        ax.set_xticks(sorted(unique_scores))

    ax.set_xlabel("Score")
    ax.set_ylabel("Task count")
    ax.set_title("Test result distribution")
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    fig.tight_layout()
    plot_path = output_dir / "score_distribution.png"
    fig.savefig(plot_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return plot_path


def render_score_distribution_by_software(summary: dict, output_dir: Path) -> list[Path]:
    output_paths: list[Path] = []
    for software, rows in sorted(summary["by_software_and_level"].items()):
        software_scores = [detail["score"] for detail in summary["details"] if detail["software"] == software]
        if not software_scores:
            continue

        fig, ax = plt.subplots(figsize=(8.5, 5.0))
        unique_scores = sorted(set(software_scores))
        if all(score in {0.0, 1.0} for score in unique_scores):
            bins = [-0.5, 0.5, 1.5]
            ax.hist(software_scores, bins=bins, color=PLOT_COLORS["score_hist"], edgecolor="white", rwidth=0.7)
            ax.set_xticks([0.0, 1.0], ["Fail (0)", "Pass (1)"])
        else:
            bin_count = min(15, max(5, len(unique_scores)))
            ax.hist(software_scores, bins=bin_count, color=PLOT_COLORS["score_hist"], edgecolor="white")
            ax.set_xticks(sorted(unique_scores))

        ax.set_xlabel("Score")
        ax.set_ylabel("Task count")
        ax.set_title(f"Result distribution: {software}")
        ax.grid(axis="y", linestyle="--", alpha=0.3)

        fig.tight_layout()
        plot_path = output_dir / f"score_distribution_{sanitize_filename(software)}.png"
        fig.savefig(plot_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        output_paths.append(plot_path)

    return output_paths


def render_visualizations(summary: dict, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    levels = get_visible_levels(summary)
    output_paths = [
        render_dashboard(summary, output_dir, levels),
        render_task_count_by_software(summary, output_dir, levels),
        render_task_count_by_level(summary, output_dir, levels),
        render_task_count_by_software_pie(summary, output_dir),
        render_score_distribution(summary, output_dir),
    ]
    output_paths.extend(render_score_distribution_by_software(summary, output_dir))
    return output_paths


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Count accuracy by software and task level for an OSWorld result folder."
    )
    parser.add_argument(
        "result_root",
        help="Path to the result root, e.g. results/<exp>/pyautogui/screenshot/<model>",
    )
    parser.add_argument(
        "--json-out",
        help="Optional path to save the summary as JSON.",
    )
    parser.add_argument(
        "--plot-out-dir",
        help="Directory to save visualization PNG files. Defaults to <result_root>/stats_visualizations.",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Disable visualization output.",
    )
    args = parser.parse_args()

    result_root = Path(args.result_root).expanduser().resolve()
    if not result_root.is_dir():
        raise SystemExit(f"Result directory does not exist: {result_root}")

    summary = collect_stats(result_root)
    print_summary(summary)

    if args.json_out:
        json_out = Path(args.json_out).expanduser().resolve()
        json_out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print()
        print(f"JSON saved to: {json_out}")

    if not args.no_plot:
        plot_out_dir = (
            Path(args.plot_out_dir).expanduser().resolve()
            if args.plot_out_dir
            else result_root / "stats_visualizations"
        )
        plot_paths = render_visualizations(summary, plot_out_dir)
        print()
        for plot_path in plot_paths:
            print(f"Plot saved to: {plot_path}")


if __name__ == "__main__":
    main()
