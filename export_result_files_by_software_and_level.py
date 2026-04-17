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


def is_success(score: float) -> bool:
    return score >= 1.0


def build_export(result_root: Path) -> dict:
    export_data: dict[str, dict[str, dict[str, list[str]]]] = {}

    for software_dir in sorted(result_root.iterdir()):
        if not software_dir.is_dir():
            continue

        software_bucket = export_data.setdefault(
            software_dir.name,
            {
                level: {"correct": [], "wrong": []}
                for level in ALL_LEVELS
            },
        )

        for task_dir in sorted(software_dir.iterdir()):
            if not task_dir.is_dir():
                continue

            result_path = task_dir / "result.txt"
            if not result_path.is_file():
                continue

            score = parse_result(result_path)
            level = extract_level(task_dir.name)
            bucket = "correct" if is_success(score) else "wrong"
            software_bucket[level][bucket].append(task_dir.name)

    return {
        "root": str(result_root),
        "results": export_data,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export correct and wrong task files grouped by software and level."
    )
    parser.add_argument(
        "result_root",
        help="Path to the result root, e.g. results/<exp>/pyautogui/screenshot/<model>",
    )
    parser.add_argument(
        "json_out",
        nargs="?",
        help=(
            "Optional path to the output JSON file. Defaults to "
            "<result_root>/result_files_by_software_and_level.json"
        ),
    )
    args = parser.parse_args()

    result_root = Path(args.result_root).expanduser().resolve()
    if not result_root.is_dir():
        raise SystemExit(f"Result directory does not exist: {result_root}")

    if args.json_out:
        json_out = Path(args.json_out).expanduser().resolve()
    else:
        json_out = result_root / "result_files_by_software_and_level.json"

    export_data = build_export(result_root)
    json_out.write_text(json.dumps(export_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"JSON saved to: {json_out}")


if __name__ == "__main__":
    main()
