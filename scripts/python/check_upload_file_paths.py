#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any


def iter_json_files(base_dir: Path) -> list[Path]:
    return sorted(path for path in base_dir.rglob("*.json") if path.is_file())


def collect_local_paths(node: Any) -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        local_path = node.get("local_path")
        if isinstance(local_path, str):
            found.append(local_path)
        for value in node.values():
            found.extend(collect_local_paths(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(collect_local_paths(item))
    return found


def extract_upload_paths(task: dict[str, Any]) -> list[str]:
    config = task.get("config", [])
    if not isinstance(config, list):
        return []

    paths: list[str] = []
    for entry in config:
        if not isinstance(entry, dict):
            continue
        if entry.get("type") != "upload_file":
            continue
        paths.extend(collect_local_paths(entry.get("parameters", {})))
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check whether upload_file local_path assets referenced by task JSON files exist."
    )
    parser.add_argument(
        "--base-dir",
        default="evaluation_examples/example_final",
        help="Directory containing task JSON files.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root used to resolve relative local_path values.",
    )
    parser.add_argument(
        "--show-ok",
        action="store_true",
        help="Also print JSON files whose upload_file assets all exist.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    base_dir = (repo_root / args.base_dir).resolve()

    if not base_dir.exists():
        print(f"Base directory does not exist: {base_dir}")
        return 2

    json_files = iter_json_files(base_dir)
    checked_files = 0
    files_with_uploads = 0
    total_refs = 0
    missing_refs = 0

    for json_file in json_files:
        checked_files += 1
        try:
            task = json.loads(json_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"JSON parse error: {json_file.relative_to(repo_root)}: {exc}")
            return 2

        upload_paths = extract_upload_paths(task)
        if not upload_paths:
            continue

        files_with_uploads += 1
        total_refs += len(upload_paths)
        missing_for_file: list[tuple[str, Path]] = []

        for local_path in upload_paths:
            resolved_path = (repo_root / local_path).resolve()
            if not resolved_path.exists():
                missing_refs += 1
                missing_for_file.append((local_path, resolved_path))

        rel_json = json_file.relative_to(repo_root)
        if missing_for_file:
            print(f"MISSING {rel_json}")
            for local_path, resolved_path in missing_for_file:
                print(f"  - {local_path}")
                print(f"    resolved: {resolved_path}")
        elif args.show_ok:
            print(f"OK {rel_json} ({len(upload_paths)} paths)")

    print(
        "\nSummary: "
        f"checked_json={checked_files}, "
        f"json_with_upload_file={files_with_uploads}, "
        f"referenced_local_paths={total_refs}, "
        f"missing_local_paths={missing_refs}"
    )

    return 1 if missing_refs else 0


if __name__ == "__main__":
    raise SystemExit(main())
