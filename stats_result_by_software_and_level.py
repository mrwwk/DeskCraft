import argparse
import ast
import json
import re
from pathlib import Path


VALID_LEVELS = ("L1", "L2", "L3")
ALL_LEVELS = VALID_LEVELS + ("UNKNOWN",)


def parse_result(result_path: Path) -> float:
    raw = result_path.read_text(encoding="utf-8").strip()
    if not raw:
        return 0.0

    try:
        return float(raw)
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
        return float(parsed)

    return 1.0 if parsed else 0.0


def extract_level(task_dir_name: str) -> str:
    match = re.search(r"(^|[_-])(L[123])(?=$|[_-])", task_dir_name)
    if match:
        return match.group(2)

    for level in VALID_LEVELS:
        if task_dir_name.endswith(f"_{level}") or task_dir_name.startswith(f"{level}_"):
            return level
    return "UNKNOWN"


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
    level_stats: dict[str, list[float]] = {level: [] for level in ALL_LEVELS}
    overall_results: list[float] = []
    detailed_rows: list[dict] = []

    for software_dir in sorted(result_root.iterdir()):
        if not software_dir.is_dir():
            continue

        for task_dir in sorted(software_dir.iterdir()):
            if not task_dir.is_dir():
                continue

            result_path = task_dir / "result.txt"
            if not result_path.is_file():
                continue

            score = parse_result(result_path)
            level = extract_level(task_dir.name)

            software_stats.setdefault(software_dir.name, []).append(score)
            level_stats[level].append(score)
            overall_results.append(score)
            detailed_rows.append(
                {
                    "software": software_dir.name,
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
    print()

    print("By level:")
    for level, stats in summary["by_level"].items():
        print(
            f"  {level}: count={stats['count']} success={stats['success']:.1f} "
            f"accuracy={stats['accuracy']:.2f}%"
        )


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


if __name__ == "__main__":
    main()
