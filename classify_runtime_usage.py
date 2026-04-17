#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path


DEFAULT_ROOT = Path(
    "results/gpt54-not_interactive—think_low/pyautogui/screenshot/"
    "api_azure_openai_gpt-5.4-2026-03-05"
)

SCRIPT_HINT_PATTERNS = [
    re.compile(pattern)
    for pattern in (
        r"\bimport\s+bpy\b",
        r"cat\s+.*<<'PY'",
        r"cat\s+.*<<\"PY\"",
        r"<<'PY'",
        r"<<\"PY\"",
        r"\bpython(?:3)?\s+-c\b",
        r"\bpython(?:3)?\b.*\s--python\b",
        r"\bblender\b.*\s--python\b",
        r"/tmp/[A-Za-z0-9_./-]+\.py\b",
        r"pyautogui\.typewrite\(['\"]import ",
        r"pyautogui\.typewrite\(['\"]from ",
        r"pyautogui\.typewrite\(['\"]def ",
        r"pyautogui\.typewrite\(['\"]class ",
        r"pyautogui\.typewrite\(['\"]PY['\"]",
    )
]

GUI_ONLY_PATTERNS = [
    re.compile(pattern)
    for pattern in (
        r"pyautogui\.moveTo\(",
        r"pyautogui\.click\(",
        r"pyautogui\.doubleClick\(",
        r"pyautogui\.rightClick\(",
        r"pyautogui\.dragTo\(",
        r"pyautogui\.hotkey\(",
        r"pyautogui\.press\(",
        r"pyautogui\.typewrite\(",
        r"time\.sleep\(",
    )
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Classify task trajectories/runtime logs by whether they likely used an external "
            "script/command workflow or only GUI actions."
        )
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=str(DEFAULT_ROOT),
        help="Directory to scan recursively. Defaults to the provided results directory.",
    )
    parser.add_argument(
        "--show-reasons",
        action="store_true",
        help="Print the matching evidence for each classified task.",
    )
    parser.add_argument(
        "--only",
        choices=["script", "gui_only", "mixed", "unknown"],
        help="Only print tasks in one class.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "csv", "json"],
        default="text",
        help="Output format. Defaults to text.",
    )
    parser.add_argument(
        "--output",
        help="Optional output file path. If omitted, prints to stdout.",
    )
    return parser.parse_args()


def iter_task_dirs(root: Path) -> list[Path]:
    task_dirs: list[Path] = []
    for path in root.rglob("runtime.log"):
        task_dirs.append(path.parent)
    return sorted(task_dirs)


def extract_text_signals(task_dir: Path) -> list[str]:
    signals: list[str] = []

    runtime_log = task_dir / "runtime.log"
    if runtime_log.is_file():
        try:
            with runtime_log.open("r", encoding="utf-8", errors="replace") as handle:
                signals.extend(line.rstrip("\n") for line in handle)
        except OSError:
            pass

    traj_path = task_dir / "traj.jsonl"
    if traj_path.is_file():
        try:
            with traj_path.open("r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    action = obj.get("action", {}).get("action")
                    if isinstance(action, str):
                        signals.append(action)
                    response = obj.get("response")
                    if isinstance(response, str) and response:
                        signals.append(response)
        except OSError:
            pass

    return signals


def classify_task(task_dir: Path) -> tuple[str, list[str]]:
    signals = extract_text_signals(task_dir)
    script_hits: list[str] = []
    gui_hits: list[str] = []

    for signal in signals:
        for pattern in SCRIPT_HINT_PATTERNS:
            if pattern.search(signal) and is_meaningful_script_hit(signal):
                script_hits.append(signal)
                break
        for pattern in GUI_ONLY_PATTERNS:
            if pattern.search(signal):
                gui_hits.append(signal)
                break

    if script_hits and gui_hits:
        return "mixed", dedupe_preserve_order(script_hits[:5] + gui_hits[:5])
    if script_hits:
        return "script", dedupe_preserve_order(script_hits[:8])
    if gui_hits:
        return "gui_only", dedupe_preserve_order(gui_hits[:8])
    return "unknown", []


def is_meaningful_script_hit(signal: str) -> bool:
    lowered = signal.lower()
    false_positive_fragments = (
        "import pyautogui",
        "import time",
        "pyautogui.typewrite('import pyautogui",
        'pyautogui.typewrite("import pyautogui',
        "pyautogui.typewrite('import time",
        'pyautogui.typewrite("import time',
    )
    return not any(fragment in lowered for fragment in false_positive_fragments)


def dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def shorten(text: str, limit: int = 160) -> str:
    compact = text.replace("\n", "\\n")
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def build_rows(root: Path, task_dirs: list[Path], only: str | None) -> tuple[list[dict[str, object]], dict[str, int]]:
    rows: list[dict[str, object]] = []
    counts = {"script": 0, "gui_only": 0, "mixed": 0, "unknown": 0}

    for task_dir in task_dirs:
        label, reasons = classify_task(task_dir)
        counts[label] += 1

        if only and label != only:
            continue

        rel_task_dir = task_dir.relative_to(root)
        rows.append(
            {
                "task_dir": rel_task_dir.as_posix() if str(rel_task_dir) != "." else ".",
                "label": label,
                "runtime_log": (task_dir / "runtime.log").relative_to(root).as_posix(),
                "traj_jsonl": (
                    (task_dir / "traj.jsonl").relative_to(root).as_posix()
                    if (task_dir / "traj.jsonl").exists()
                    else ""
                ),
                "reason_count": len(reasons),
                "reasons": reasons,
            }
        )

    return rows, counts


def render_text(rows: list[dict[str, object]], counts: dict[str, int], total_tasks: int, show_reasons: bool) -> str:
    lines: list[str] = []
    for row in rows:
        lines.append(f"[{row['label']}] {row['task_dir']}")
        if show_reasons:
            for reason in row["reasons"]:
                lines.append(f"  {shorten(reason)}")

    if lines:
        lines.append("")
    lines.append(
        "Summary: "
        f"script={counts['script']}, mixed={counts['mixed']}, "
        f"gui_only={counts['gui_only']}, unknown={counts['unknown']}, total={total_tasks}"
    )
    return "\n".join(lines)


def render_json(rows: list[dict[str, object]], counts: dict[str, int], total_tasks: int, show_reasons: bool) -> str:
    serializable_rows = []
    for row in rows:
        item = dict(row)
        if not show_reasons:
            item["reasons"] = []
        serializable_rows.append(item)

    payload = {
        "summary": {
            "script": counts["script"],
            "mixed": counts["mixed"],
            "gui_only": counts["gui_only"],
            "unknown": counts["unknown"],
            "total": total_tasks,
            "returned": len(serializable_rows),
        },
        "tasks": serializable_rows,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def render_csv(rows: list[dict[str, object]], show_reasons: bool) -> str:
    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=["task_dir", "label", "runtime_log", "traj_jsonl", "reason_count", "reasons"],
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                "task_dir": row["task_dir"],
                "label": row["label"],
                "runtime_log": row["runtime_log"],
                "traj_jsonl": row["traj_jsonl"],
                "reason_count": row["reason_count"],
                "reasons": " || ".join(shorten(item, 400) for item in row["reasons"]) if show_reasons else "",
            }
        )
    return buffer.getvalue()


def write_output(text: str, output_path: str | None) -> None:
    if output_path is None:
        print(text)
        return

    path = Path(output_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()

    if not root.exists():
        print(f"Directory does not exist: {root}", file=sys.stderr)
        return 1

    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 1

    task_dirs = iter_task_dirs(root)
    if not task_dirs:
        print(f"No runtime.log files found under: {root}")
        return 0

    rows, counts = build_rows(root, task_dirs, args.only)

    if args.format == "json":
        output_text = render_json(rows, counts, len(task_dirs), args.show_reasons)
    elif args.format == "csv":
        output_text = render_csv(rows, args.show_reasons)
    else:
        output_text = render_text(rows, counts, len(task_dirs), args.show_reasons)

    write_output(output_text, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
