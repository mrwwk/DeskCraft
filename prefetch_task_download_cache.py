#!/usr/bin/env python3
"""Prefetch task download assets into the local OSWorld cache.

This script scans task JSON files under one or more directories, extracts
`config[].type == "download"` entries, and downloads the referenced files into
the same task-scoped cache layout used by `desktop_env.controllers.setup`:

    cache/<task_id>/<uuid5(url)>_<basename(path)>

By default it scans:
    - evaluation_examples/example_final
    - evaluation_examples/example_backup
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import logging
import os
import sys
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import requests


DEFAULT_INPUT_DIRS = [
    "evaluation_examples/example_final",
    "evaluation_examples/example_backup",
]


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("prefetch_task_download_cache")


@dataclass(frozen=True)
class DownloadEntry:
    task_id: str
    task_file: str
    url: str
    remote_path: str

    @property
    def cache_filename(self) -> str:
        return f"{uuid.uuid5(uuid.NAMESPACE_URL, self.url)}_{os.path.basename(self.remote_path)}"

    def cache_path(self, cache_dir: str) -> str:
        return os.path.join(cache_dir, self.task_id, self.cache_filename)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prefetch OSWorld task download assets into the local cache."
    )
    parser.add_argument(
        "--input-dir",
        action="append",
        dest="input_dirs",
        help=(
            "Directory to scan recursively for task JSON files. "
            "Can be specified multiple times. Defaults to example_final and example_backup."
        ),
    )
    parser.add_argument(
        "--cache-dir",
        default="cache",
        help="Base cache directory. Task subdirectories will be created automatically.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Maximum number of concurrent downloads.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print which files would be downloaded without downloading them.",
    )
    parser.add_argument(
        "--include-existing",
        action="store_true",
        help="Include entries that already exist in cache in the printed plan/statistics.",
    )
    parser.add_argument(
        "--disable-env-proxy",
        action="store_true",
        help="Ignore HTTP(S)_PROXY environment variables for these downloads.",
    )
    return parser.parse_args()


def iter_json_files(input_dirs: Iterable[str]) -> list[Path]:
    json_files: list[Path] = []

    for raw_dir in input_dirs:
        path = Path(raw_dir)
        if not path.exists():
            logger.warning("Input directory does not exist, skipping: %s", path)
            continue
        if not path.is_dir():
            logger.warning("Input path is not a directory, skipping: %s", path)
            continue
        json_files.extend(sorted(path.rglob("*.json")))

    return json_files


def extract_downloads(task_file: Path) -> list[DownloadEntry]:
    try:
        with task_file.open("r", encoding="utf-8") as f:
            task_data = json.load(f)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse JSON in %s: %s", task_file, exc)
        return []
    except OSError as exc:
        logger.error("Failed to read %s: %s", task_file, exc)
        return []

    task_id = task_data.get("id")
    if not task_id:
        logger.warning("Task file missing id, skipping: %s", task_file)
        return []

    entries: list[DownloadEntry] = []
    config = task_data.get("config", [])
    if not isinstance(config, list):
        logger.warning("Task config is not a list, skipping: %s", task_file)
        return []

    for step in config:
        if not isinstance(step, dict) or step.get("type") != "download":
            continue

        files = step.get("parameters", {}).get("files", [])
        if not isinstance(files, list):
            continue

        for file_info in files:
            if not isinstance(file_info, dict):
                continue
            url = file_info.get("url")
            remote_path = file_info.get("path")
            if not url or not remote_path:
                logger.warning(
                    "Skipping malformed download entry in %s: %s",
                    task_file,
                    file_info,
                )
                continue
            entries.append(
                DownloadEntry(
                    task_id=task_id,
                    task_file=str(task_file),
                    url=url,
                    remote_path=remote_path,
                )
            )

    return entries


def collect_downloads(
    input_dirs: Iterable[str],
    cache_dir: str,
    include_existing: bool,
) -> tuple[list[DownloadEntry], int]:
    json_files = iter_json_files(input_dirs)
    logger.info("Found %d JSON files to scan", len(json_files))

    downloads: list[DownloadEntry] = []
    seen_keys: set[tuple[str, str]] = set()
    already_cached = 0

    for task_file in json_files:
        for entry in extract_downloads(task_file):
            dedupe_key = (entry.task_id, entry.cache_filename)
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)

            cache_path = entry.cache_path(cache_dir)
            if os.path.exists(cache_path):
                already_cached += 1
                if include_existing:
                    downloads.append(entry)
                continue

            downloads.append(entry)

    return downloads, already_cached


def build_session(disable_env_proxy: bool) -> requests.Session:
    session = requests.Session()
    if disable_env_proxy:
        session.trust_env = False
    return session


def download_entry(
    entry: DownloadEntry,
    cache_dir: str,
    disable_env_proxy: bool,
    lock: threading.Lock,
) -> tuple[bool, str]:
    cache_path = entry.cache_path(cache_dir)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)

    if os.path.exists(cache_path):
        return True, f"cached {cache_path}"

    error: Exception | None = None
    max_retries = 3

    for attempt in range(1, max_retries + 1):
        session = build_session(disable_env_proxy)
        try:
            with session.get(entry.url, stream=True, timeout=300) as response:
                response.raise_for_status()
                expected_size = int(response.headers.get("content-length", 0))

                downloaded_size = 0
                with open(cache_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if not chunk:
                            continue
                        f.write(chunk)
                        downloaded_size += len(chunk)

                actual_size = os.path.getsize(cache_path)
                if expected_size > 0 and actual_size != expected_size:
                    raise RuntimeError(
                        f"Download incomplete. Expected {expected_size} bytes, got {actual_size} bytes"
                    )

                return True, f"downloaded {cache_path} ({actual_size} bytes)"
        except Exception as exc:  # noqa: BLE001
            error = exc
            if os.path.exists(cache_path):
                try:
                    os.remove(cache_path)
                except OSError:
                    pass
            with lock:
                logger.warning(
                    "Attempt %d/%d failed for %s: %s",
                    attempt,
                    max_retries,
                    entry.url,
                    exc,
                )
        finally:
            session.close()

    return False, f"failed {entry.url}: {error}"


def main() -> int:
    args = parse_args()
    input_dirs = args.input_dirs or DEFAULT_INPUT_DIRS
    cache_dir = args.cache_dir

    os.makedirs(cache_dir, exist_ok=True)

    downloads, already_cached = collect_downloads(
        input_dirs=input_dirs,
        cache_dir=cache_dir,
        include_existing=args.include_existing,
    )

    logger.info("Input directories: %s", ", ".join(input_dirs))
    logger.info("Cache directory: %s", cache_dir)
    logger.info("Entries already cached: %d", already_cached)
    logger.info("Entries selected: %d", len(downloads))

    if not downloads:
        logger.info("No files need downloading.")
        return 0

    for entry in downloads:
        status = "exists" if os.path.exists(entry.cache_path(cache_dir)) else "missing"
        logger.info(
            "[%s] task=%s file=%s url=%s source=%s",
            status,
            entry.task_id,
            entry.cache_filename,
            entry.url,
            entry.task_file,
        )

    if args.dry_run:
        logger.info("Dry run enabled, no files were downloaded.")
        return 0

    lock = threading.Lock()
    succeeded = 0
    failed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        future_map = {
            executor.submit(
                download_entry,
                entry,
                cache_dir,
                args.disable_env_proxy,
                lock,
            ): entry
            for entry in downloads
            if not os.path.exists(entry.cache_path(cache_dir))
        }

        for future in concurrent.futures.as_completed(future_map):
            entry = future_map[future]
            try:
                ok, message = future.result()
            except Exception as exc:  # noqa: BLE001
                ok = False
                message = f"failed {entry.url}: {exc}"

            if ok:
                succeeded += 1
                logger.info("SUCCESS task=%s %s", entry.task_id, message)
            else:
                failed += 1
                logger.error("FAILED task=%s %s", entry.task_id, message)

    logger.info("Download complete. succeeded=%d failed=%d", succeeded, failed)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
