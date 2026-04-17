#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find subdirectories that do not contain a target file."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to inspect. Defaults to the current directory.",
    )
    parser.add_argument(
        "--filename",
        default="result.txt",
        help="Target filename to check. Defaults to result.txt.",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=2,
        help="Directory depth to check relative to the root. Defaults to 2.",
    )
    return parser.parse_args()


def iter_subdirectories(root: Path, depth: int) -> list[Path]:
    if depth < 1:
        raise ValueError("depth must be >= 1")

    return sorted(path for path in root.glob("*/" * depth) if path.is_dir())


def main() -> int:
    args = parse_args()
    root = Path(args.directory).expanduser().resolve()

    if not root.exists():
        print(f"Directory does not exist: {root}", file=sys.stderr)
        return 1

    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 1

    if args.depth < 1:
        print("--depth must be >= 1", file=sys.stderr)
        return 1

    missing_dirs = [
        path for path in iter_subdirectories(root, args.depth) if not (path / args.filename).is_file()
    ]

    if not missing_dirs:
        print(f"All checked directories contain {args.filename}.")
        return 0

    print(f"Directories missing {args.filename}:")
    for path in missing_dirs:
        print(path.relative_to(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
