#!/usr/bin/env python3
"""Offline detector for answer-leakage in DeskCraft file-compare tasks.

For tasks that upload an initial file (``upload_file``) and compare the agent
result against a gold file (``evaluator.expected.type == cache_file``), this
script runs the task's evaluator metric against *initial vs gold* without a VM.
If the initial file already scores at or above the threshold (default 1.0), the
task is flagged as answer leakage — the agent can pass without doing the work.

Also flags tasks where initial and gold files are byte-identical (md5 match).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import inspect
import json
import os
import sys
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

FILE_COMPARE_FUNCS = frozenset(
    {
        "compare_table",
        "compare_pptx_files",
        "compare_docx_files",
        "compare_docx_content_and_format",
    }
)


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _md5_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve_gold_path(
    expected_path: str, task_dir: Path, cache_dir: Path
) -> Path | None:
    """Mirror ``get_cache_file``: cache_dir first, then task_dir fallback."""
    candidates = [
        cache_dir / expected_path,
        task_dir / expected_path,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _collect_upload_files(task_config: dict, project_root: Path) -> list[dict[str, str]]:
    uploads: list[dict[str, str]] = []
    for step in task_config.get("config", []):
        if step.get("type") != "upload_file":
            continue
        for f in step.get("parameters", {}).get("files", []):
            local_path = f.get("local_path", "")
            vm_path = f.get("path", "")
            if not local_path:
                continue
            abs_local = (project_root / local_path).resolve()
            uploads.append(
                {
                    "local_path": str(abs_local),
                    "local_path_rel": local_path,
                    "vm_path": vm_path,
                    "vm_basename": os.path.basename(vm_path),
                }
            )
    return uploads


def _result_basename(evaluator: dict) -> str | None:
    result = evaluator.get("result")
    if not isinstance(result, dict):
        return None
    dest = result.get("dest") or result.get("path")
    if not dest:
        return None
    return os.path.basename(dest)


def _match_initial_to_result(
    uploads: list[dict[str, str]], evaluator: dict
) -> dict[str, str] | None:
    if not uploads:
        return None
    if len(uploads) == 1:
        return uploads[0]

    result_base = _result_basename(evaluator)
    if result_base:
        for upload in uploads:
            if upload["vm_basename"] == result_base:
                return upload

    # Fallback: match by filename stem against gold/result dest
    expected = evaluator.get("expected", {})
    if isinstance(expected, dict):
        gold_base = os.path.basename(expected.get("path", ""))
        if gold_base:
            gold_stem = Path(gold_base).stem.replace("_gold", "")
            for upload in uploads:
                upload_stem = Path(upload["vm_basename"]).stem
                if upload_stem == gold_stem or gold_stem.startswith(upload_stem):
                    return upload

    return uploads[0]


def _load_metric(evaluator_py: Path, func_name: str):
    module_name = f"leakage_metric_{hash(evaluator_py) & 0xFFFFFFFF:08x}"
    spec = importlib.util.spec_from_file_location(module_name, str(evaluator_py))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import {evaluator_py}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    metric = getattr(module, func_name)
    if not callable(metric):
        raise TypeError(f"{func_name} is not callable in {evaluator_py}")
    return metric


def _metric_expects_expected(metric) -> bool:
    positional = [
        p
        for p in inspect.signature(metric).parameters.values()
        if p.kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
    ]
    return len(positional) >= 2


def _run_metric(metric, initial_path: str, gold_path: str, options: dict) -> float:
    options = options or {}
    if _metric_expects_expected(metric):
        return float(metric(initial_path, gold_path, **options))
    return float(metric(initial_path, **options))


def _is_candidate(task_config: dict) -> tuple[bool, str | None]:
    evaluator = task_config.get("evaluator", {})
    if not isinstance(evaluator, dict):
        return False, "no evaluator"

    func = evaluator.get("func")
    if isinstance(func, list):
        return False, "multi-metric evaluator (list func)"
    if func not in FILE_COMPARE_FUNCS:
        return False, f"func not in file-compare set: {func!r}"

    expected = evaluator.get("expected")
    if not isinstance(expected, dict):
        return False, "expected is not a dict"
    if expected.get("type") != "cache_file":
        return False, f"expected type is {expected.get('type')!r}"

    has_upload = any(
        step.get("type") == "upload_file"
        for step in task_config.get("config", [])
    )
    if not has_upload:
        return False, "no upload_file in config"

    return True, None


def _classify_leakage(
    score: float | None,
    identical_bytes: bool,
    threshold: float,
    include_partial: bool,
) -> tuple[bool, str | None]:
    if identical_bytes:
        return True, "identical_bytes"
    if score is None:
        return False, None
    if score >= threshold:
        return True, "full_leak"
    if include_partial and score > 0.0:
        return True, "partial_leak"
    return False, None


def scan_task(
    task_json_path: str,
    project_root: str,
    cache_dir: str,
    threshold: float,
    include_partial: bool,
) -> dict[str, Any]:
    """Scan a single task. Returns a result record (never raises)."""
    project_root_p = Path(project_root).resolve()
    cache_dir_p = Path(cache_dir).resolve()
    task_json = Path(task_json_path).resolve()
    task_dir = task_json.parent
    domain = task_dir.parent.name
    task_folder = task_dir.name

    record: dict[str, Any] = {
        "task_id": None,
        "domain": domain,
        "task_dir": str(task_dir.relative_to(project_root_p)),
        "task_folder": task_folder,
        "func": None,
        "initial_path": None,
        "initial_path_rel": None,
        "gold_path": None,
        "gold_path_rel": None,
        "score": None,
        "md5_initial": None,
        "md5_gold": None,
        "identical_bytes": False,
        "leakage": False,
        "leakage_type": None,
        "instruction": None,
        "status": "ok",
        "skip_reason": None,
        "error": None,
    }

    try:
        task_config = _load_json(task_json)
        record["task_id"] = task_config.get("id")
        record["instruction"] = task_config.get("instruction", "")

        is_cand, skip_reason = _is_candidate(task_config)
        if not is_cand:
            record["status"] = "skipped"
            record["skip_reason"] = skip_reason
            return record

        evaluator = task_config["evaluator"]
        func_name = evaluator["func"]
        record["func"] = func_name

        uploads = _collect_upload_files(task_config, project_root_p)
        upload = _match_initial_to_result(uploads, evaluator)
        if upload is None:
            record["status"] = "skipped"
            record["skip_reason"] = "no upload files found"
            return record

        initial_path = Path(upload["local_path"])
        if not initial_path.is_file():
            record["status"] = "skipped"
            record["skip_reason"] = f"initial file not found: {upload['local_path_rel']}"
            return record

        expected_path = evaluator["expected"]["path"]
        gold_path = _resolve_gold_path(expected_path, task_dir, cache_dir_p)
        if gold_path is None:
            record["status"] = "skipped"
            record["skip_reason"] = f"gold file not found: {expected_path}"
            return record

        record["initial_path"] = str(initial_path)
        record["initial_path_rel"] = upload["local_path_rel"]
        record["gold_path"] = str(gold_path)
        try:
            record["gold_path_rel"] = str(gold_path.relative_to(project_root_p))
        except ValueError:
            record["gold_path_rel"] = str(gold_path)

        md5_initial = _md5_file(initial_path)
        md5_gold = _md5_file(gold_path)
        record["md5_initial"] = md5_initial
        record["md5_gold"] = md5_gold
        identical = bool(md5_initial and md5_gold and md5_initial == md5_gold)
        record["identical_bytes"] = identical

        evaluator_py = task_dir / evaluator.get("file", "evaluator.py")
        if not evaluator_py.is_file():
            record["status"] = "error"
            record["error"] = f"evaluator.py not found: {evaluator_py}"
            return record

        metric = _load_metric(evaluator_py, func_name)
        options = evaluator.get("options") or {}
        score = _run_metric(metric, str(initial_path), str(gold_path), options)
        record["score"] = score

        leakage, leakage_type = _classify_leakage(
            score, identical, threshold, include_partial
        )
        record["leakage"] = leakage
        record["leakage_type"] = leakage_type

    except Exception as exc:
        record["status"] = "error"
        record["error"] = f"{type(exc).__name__}: {exc}"
        record["traceback"] = traceback.format_exc()

    return record


def discover_tasks(tasks_dir: Path, domain: str) -> list[Path]:
    task_jsons: list[Path] = []
    if not tasks_dir.is_dir():
        raise FileNotFoundError(f"tasks-dir not found: {tasks_dir}")

    domains = sorted(d.name for d in tasks_dir.iterdir() if d.is_dir())
    if domain != "all":
        if domain not in domains:
            raise ValueError(f"unknown domain {domain!r}; available: {domains}")
        domains = [domain]

    for dom in domains:
        dom_dir = tasks_dir / dom
        for task_dir in sorted(dom_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            task_json = task_dir / "task.json"
            if task_json.is_file():
                task_jsons.append(task_json)
    return task_jsons


def _scan_worker(args: tuple) -> dict[str, Any]:
    return scan_task(*args)


def run_scan(
    project_root: Path,
    tasks_dir: Path,
    cache_dir: Path,
    domain: str,
    threshold: float,
    include_partial: bool,
    workers: int,
) -> list[dict[str, Any]]:
    task_jsons = discover_tasks(tasks_dir, domain)
    worker_args = [
        (
            str(tp),
            str(project_root),
            str(cache_dir),
            threshold,
            include_partial,
        )
        for tp in task_jsons
    ]

    results: list[dict[str, Any]] = []
    if workers <= 1:
        for args in worker_args:
            results.append(scan_task(*args))
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_scan_worker, a): a for a in worker_args}
            for fut in as_completed(futures):
                results.append(fut.result())

    # Stable sort: leaked first, then domain, then task_id
    results.sort(
        key=lambda r: (
            not r.get("leakage", False),
            r.get("domain", ""),
            r.get("task_id") or r.get("task_folder", ""),
        )
    )
    return results


def _summarize(results: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "total_tasks_scanned": len(results),
        "candidates_scanned": 0,
        "skipped": 0,
        "errors": 0,
        "leaked": 0,
        "full_leak": 0,
        "identical_bytes": 0,
        "partial_leak": 0,
        "clean": 0,
    }
    for r in results:
        if r.get("status") == "skipped":
            summary["skipped"] += 1
            continue
        if r.get("status") == "error":
            summary["errors"] += 1
            continue
        if r.get("skip_reason"):
            summary["skipped"] += 1
            continue

        summary["candidates_scanned"] += 1
        if r.get("leakage"):
            summary["leaked"] += 1
            lt = r.get("leakage_type")
            if lt == "full_leak":
                summary["full_leak"] += 1
            elif lt == "identical_bytes":
                summary["identical_bytes"] += 1
            elif lt == "partial_leak":
                summary["partial_leak"] += 1
        else:
            summary["clean"] += 1
    return summary


CSV_FIELDS = [
    "task_id",
    "domain",
    "task_dir",
    "func",
    "score",
    "leakage",
    "leakage_type",
    "identical_bytes",
    "initial_path_rel",
    "gold_path_rel",
    "md5_initial",
    "md5_gold",
    "status",
    "skip_reason",
    "error",
    "instruction",
]


def write_csv(path: Path, results: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            writer.writerow({k: r.get(k, "") for k in CSV_FIELDS})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def print_summary(summary: dict[str, int], leaked: list[dict[str, Any]]) -> None:
    print("\n========== Answer Leakage Scan Summary ==========")
    for key, val in summary.items():
        print(f"  {key}: {val}")
    if leaked:
        print("\n--- Leaked tasks ---")
        for r in leaked:
            print(
                f"  [{r.get('leakage_type')}] {r.get('domain')}/{r.get('task_folder')} "
                f"score={r.get('score')} identical={r.get('identical_bytes')}"
            )
    print("=================================================\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detect answer leakage in DeskCraft file-compare tasks."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=_PROJECT_ROOT,
        help="DeskCraft project root (default: auto-detected)",
    )
    parser.add_argument(
        "--tasks-dir",
        type=Path,
        default=Path("evaluation_examples/examples_per_task"),
        help="Directory containing per-domain task folders",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("cache"),
        help="Cache directory for initial/gold file lookup",
    )
    parser.add_argument(
        "--domain",
        default="all",
        help="Domain to scan (all | calc | impr | writ | ...)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=1.0,
        help="Score threshold for full_leak (default: 1.0)",
    )
    parser.add_argument(
        "--include-partial",
        action="store_true",
        help="Also flag 0 < score < threshold as partial_leak",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Parallel workers (default: 4; use 1 for serial)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/answer_leakage_report.json"),
        help="Output JSON report path (CSV written alongside)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    tasks_dir = (project_root / args.tasks_dir).resolve()
    cache_dir = (project_root / args.cache_dir).resolve()
    output_json = (
        args.output if args.output.is_absolute() else (project_root / args.output)
    ).resolve()
    output_csv = output_json.with_suffix(".csv")

    print(f"Project root: {project_root}")
    print(f"Tasks dir:    {tasks_dir}")
    print(f"Cache dir:    {cache_dir}")
    print(f"Domain:       {args.domain}")
    print(f"Threshold:    {args.threshold}")
    print(f"Workers:      {args.workers}")

    results = run_scan(
        project_root=project_root,
        tasks_dir=tasks_dir,
        cache_dir=cache_dir,
        domain=args.domain,
        threshold=args.threshold,
        include_partial=args.include_partial,
        workers=args.workers,
    )

    summary = _summarize(results)
    leaked = [r for r in results if r.get("leakage")]

    payload = {
        "summary": summary,
        "threshold": args.threshold,
        "domain": args.domain,
        "leaked_tasks": leaked,
        "all_results": results,
    }

    write_json(output_json, payload)
    write_csv(output_csv, results)
    print_summary(summary, leaked)
    print(f"JSON report: {output_json}")
    print(f"CSV report:  {output_csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
