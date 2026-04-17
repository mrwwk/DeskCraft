#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


DEFAULT_ROOT = Path(
    "results/gpt54-not_interactive—think_low/pyautogui/screenshot/"
    "api_azure_openai_gpt-5.4-2026-03-05"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find successful task samples that were classified as using scripts."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=str(DEFAULT_ROOT),
        help="Results root directory. Defaults to the provided GPT-5.4 results directory.",
    )
    parser.add_argument(
        "--output",
        help="Optional output JSON path. Defaults to <root>/successful_script_samples.json.",
    )
    return parser.parse_args()


def load_result_score(task_dir: Path) -> float | None:
    result_path = task_dir / "result.txt"
    if not result_path.is_file():
        return None

    try:
        return float(result_path.read_text(encoding="utf-8", errors="replace").strip())
    except ValueError:
        return None


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()

    if not root.exists():
        print(f"Directory does not exist: {root}", file=sys.stderr)
        return 1

    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 1

    payload: dict[str, list[str]] = {}
    total_matches = 0

    for subdir in sorted(path for path in root.iterdir() if path.is_dir()):
        label_path = subdir / "runtime_usage_by_label.json"
        if not label_path.is_file():
            continue

        try:
            label_data = json.loads(label_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        successful_mixed: list[str] = []
        for task_name in label_data.get("mixed", []):
            score = load_result_score(subdir / task_name)
            if score == 1.0:
                successful_mixed.append(task_name)

        if successful_mixed:
            payload[subdir.name] = successful_mixed
            total_matches += len(successful_mixed)

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else root / "successful_script_samples.json"
    )
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(output_path)
    print(f"Matched {total_matches} successful mixed/script sample(s) across {len(payload)} subdir(s).")
    for subdir_name, tasks in payload.items():
        print(f"{subdir_name}: {len(tasks)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
