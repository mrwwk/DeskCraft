#!/usr/bin/env python3
"""Offline re-scorer for revised (revise_task) evaluators.

For each task result directory that contains a ``revise_task/`` produced by
``mini-osworld/scripts/repair_evaluators_with_codebuddy.py``, this script
re-invokes the *revised* evaluator against the saved evaluator artifacts and
reports the new score alongside the original saved score. No VM and no agent
are needed: the result/expected states were captured at run time into
``evaluator/metrics/<i>/inputs/`` and are reused here.

Key handling of ``expected``:
  - ``rule`` type: the revised ``evaluator.expected.rules`` from
    ``revise_task/task.json`` is used directly (this is the common repair —
    e.g. correcting path formats / thresholds in the rules). Marked
    ``expected_recomputed=True``.
  - other types (``cache_file``/``vm_file``/``cloud_file``) or missing: the
    saved ``inputs/expected.json`` is deserialized and reused (the referenced
    file was copied into ``inputs/files/`` at run time). Marked
    ``expected_recomputed=False``.

``result_state`` is always taken from the saved ``inputs/result.json`` (the
agent's artifact — revisions do not change the result getter).

Multi-metric tasks (``evaluator.func`` is a list) are aligned by index against
the saved ``metrics/<i>/`` directories.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import inspect
import json
import os
import sys
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

# Ensure the DeskCraft project root (parent of scripts/python/) is importable so
# that revised evaluator.py files that import ``desktop_env`` helpers resolve.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def deserialize_value(data: Any, inputs_dir: Path) -> Any:
    """Mirror of ``artifacts.py`` replay ``deserialize_value``: resolve saved
    file references into absolute paths within ``inputs_dir``."""
    if data is None:
        return None
    if isinstance(data, dict) and data.get("__type__") == "file":
        return str(inputs_dir / data["saved_as"])
    if isinstance(data, dict) and data.get("__type__") == "text_file":
        return (inputs_dir / data["saved_as"]).read_text(encoding="utf-8")
    if isinstance(data, dict) and data.get("__type__") == "repr":
        return data.get("value")
    if isinstance(data, list):
        return [deserialize_value(item, inputs_dir) for item in data]
    if isinstance(data, dict):
        return {key: deserialize_value(value, inputs_dir) for key, value in data.items()}
    return data


def _load_metric_module(revised_evaluator_py: Path):
    """Load ``revise_task/evaluator.py`` as an isolated module."""
    module_name = f"revised_evaluator_{revised_evaluator_py.parent.parent.name}"
    spec = importlib.util.spec_from_file_location(module_name, str(revised_evaluator_py))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import {revised_evaluator_py}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _as_list(value: Any, length: int) -> list:
    """Normalize a scalar-or-list evaluator config field to a list of ``length``."""
    if value is None:
        return [None] * length
    if isinstance(value, list):
        if len(value) != length:
            raise ValueError(f"list length {len(value)} != metric count {length}")
        return value
    # scalar dict/str/etc. -> broadcast (only valid for single-metric)
    if length == 1:
        return [value]
    raise ValueError(f"scalar value for multi-metric ({length}) field")


def _combine_scores(scores: list[float], conj: str) -> float:
    if not scores:
        return 0.0
    if conj == "or":
        return float(max(scores))
    # "and": any 0 -> 0, else mean
    if any(s == 0.0 for s in scores):
        return 0.0
    return float(sum(scores) / len(scores))


def _resolve_score(
    scores: list[float], missing_indices: list[int], conj: str
) -> tuple[float | None, str]:
    """Determine the revised score and how determinable it is.

    Saved artifacts may be incomplete because the original evaluation
    short-circuited (conj="and" stops at the first 0; conj="or" stops at the
    first 1). When inputs for some metrics are missing we can still determine
    the score in some cases; otherwise we mark it inconclusive (needs a full
    re-run).

    Returns (score_or_None, status) where status is one of:
      - "complete": all metrics scored.
      - "incomplete_determined": some inputs missing, but the combine result is
        already fixed by the scored subset (conj="and" with a 0, or conj="or"
        with a 1).
      - "incomplete_inconclusive": some inputs missing and the result cannot be
        determined from the scored subset alone.
    """
    if not missing_indices:
        return _combine_scores(scores, conj), "complete"
    # Incomplete saved artifacts.
    if conj == "or":
        if any(s >= 1.0 for s in scores):
            return 1.0, "incomplete_determined"
        return None, "incomplete_inconclusive"
    # conj == "and"
    if any(s == 0.0 for s in scores):
        return 0.0, "incomplete_determined"
    return None, "incomplete_inconclusive"


def _resolve_expected(revised_expected_cfg: Any | None, saved_expected_path: Path, inputs_dir: Path) -> tuple[Any, bool]:
    """Return (expected_state, recomputed_flag).

    - rule type -> use revised cfg's rules dict (recomputed)
    - None      -> (None, False)
    - other     -> deserialize saved expected.json (fallback)
    """
    if revised_expected_cfg is None:
        return None, False
    if isinstance(revised_expected_cfg, dict) and revised_expected_cfg.get("type") == "rule":
        return revised_expected_cfg.get("rules"), True
    if not saved_expected_path.is_file():
        return None, False
    return deserialize_value(_load_json(saved_expected_path), inputs_dir), False


def rescore_task(task_dir: Path) -> dict:
    """Re-score a single task result directory using its revise_task evaluator.

    Returns a result record. Never raises — exceptions are captured into
    ``error``.
    """
    record: dict[str, Any] = {
        "task_dir": str(task_dir),
        "domain": task_dir.parent.name,
        "task_id": task_dir.name,
    }
    try:
        revise_dir = task_dir / "revise_task"
        revised_task_path = revise_dir / "task.json"
        revised_evaluator_py = revise_dir / "evaluator.py"
        if not revised_task_path.is_file() or not revised_evaluator_py.is_file():
            record["error"] = "missing revise_task/task.json or revise_task/evaluator.py"
            return record

        revised_task = _load_json(revised_task_path)
        evaluator = revised_task.get("evaluator")
        if not isinstance(evaluator, dict):
            record["error"] = "revise_task/task.json has no evaluator dict"
            return record

        funcs = evaluator.get("func")
        func_list = [funcs] if isinstance(funcs, str) else list(funcs or [])
        n = len(func_list)
        if n == 0:
            record["error"] = "evaluator.func missing"
            return record

        if func_list == ["infeasible"]:
            record["original_score"] = None
            record["revised_score"] = None
            record["delta"] = 0.0
            record["num_metrics"] = 0
            record["expected_recomputed"] = False
            record["note"] = "infeasible evaluator"
            return record

        conj = evaluator.get("conj", "and")
        expected_cfg = evaluator.get("expected")
        options_cfg = evaluator.get("options")
        expected_list = _as_list(expected_cfg, n)
        options_list = _as_list(options_cfg if options_cfg is not None else [{}] * n, n)

        # Original saved score
        manifest_path = task_dir / "evaluator" / "manifest.json"
        original_score = None
        if manifest_path.is_file():
            original_score = _load_json(manifest_path).get("score")

        # Load revised metric module
        module = _load_metric_module(revised_evaluator_py)

        metrics_root = task_dir / "evaluator" / "metrics"
        expected_recomputed_any = False
        per_metric: list[dict] = []
        scored_indices: list[int] = []
        scores: list[float] = []
        missing_indices: list[int] = []

        for i in range(n):
            func_name = func_list[i]
            metric_dir = metrics_root / str(i)
            inputs_dir = metric_dir / "inputs"
            result_path = inputs_dir / "result.json"
            if not result_path.is_file():
                # Saved artifacts incomplete here (original eval short-circuited
                # via conj="and"/"or" before reaching this metric). Record and
                # continue; determinability is resolved below.
                missing_indices.append(i)
                per_metric.append({"func": func_name, "score": None, "missing_inputs": True})
                continue

            result_state = deserialize_value(_load_json(result_path), inputs_dir)
            expected_state, recomputed = _resolve_expected(
                expected_list[i], inputs_dir / "expected.json", inputs_dir
            )
            if recomputed:
                expected_recomputed_any = True
            options = options_list[i] or {}

            metric_fn = getattr(module, func_name, None)
            if not callable(metric_fn):
                raise AttributeError(f"revised evaluator.py defines no callable {func_name}")

            positional = [
                p for p in inspect.signature(metric_fn).parameters.values()
                if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            ]
            # Suppress noisy stdout/stderr from metric functions (e.g. "Result
            # file not found: FAIL") so the report stays readable.
            with open(os.devnull, "w") as devnull, contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
                if len(positional) >= 2:
                    score = float(metric_fn(result_state, expected_state, **options))
                else:
                    score = float(metric_fn(result_state, **options))
            scores.append(score)
            scored_indices.append(i)
            per_metric.append({"func": func_name, "score": score, "expected_recomputed": recomputed})

        # Resolve revised score + determinability status.
        revised_score, status = _resolve_score(scores, missing_indices, conj)

        record["original_score"] = float(original_score) if original_score is not None else None
        record["revised_score"] = revised_score
        record["delta"] = (revised_score - record["original_score"]) if revised_score is not None else None
        record["num_metrics"] = n
        record["num_scored"] = len(scores)
        record["num_missing_inputs"] = len(missing_indices)
        record["status"] = status
        record["expected_recomputed"] = expected_recomputed_any
        record["metrics"] = per_metric
    except Exception as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
        record["traceback"] = traceback.format_exc(limit=3)
    return record


def _find_revised_task_dirs(results_root: Path, domain: str | None) -> list[Path]:
    """Find ``<results_root>/<domain>/<task_id>/`` dirs that contain revise_task."""
    task_dirs: list[Path] = []
    for domain_dir in sorted(results_root.iterdir()):
        if not domain_dir.is_dir():
            continue
        if domain is not None and domain_dir.name != domain:
            continue
        for task_dir in sorted(domain_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            if (task_dir / "revise_task" / "task.json").is_file() and (
                task_dir / "revise_task" / "evaluator.py"
            ).is_file():
                task_dirs.append(task_dir)
    return task_dirs


def main() -> int:
    parser = argparse.ArgumentParser(description="Re-score revised (revise_task) evaluators offline.")
    parser.add_argument("results_root", type=Path, help="Root containing <domain>/<task_id>/ result dirs.")
    parser.add_argument("--domain", default=None, help="Only score this domain (default: all).")
    parser.add_argument("--output", type=Path, default=None, help="Write JSON report here.")
    parser.add_argument("--concurrency", type=int, default=4, help="Parallel workers.")
    parser.add_argument("--verbose", action="store_true", help="Print per-task lines.")
    args = parser.parse_args()

    if not args.results_root.is_dir():
        print(f"ERROR: results_root not a directory: {args.results_root}", file=sys.stderr)
        return 1

    task_dirs = _find_revised_task_dirs(args.results_root, args.domain)
    print(f"Found {len(task_dirs)} revised task dirs under {args.results_root}"
          + (f" (domain={args.domain})" if args.domain else ""))

    records: list[dict] = []
    if args.concurrency <= 1:
        for td in task_dirs:
            rec = rescore_task(td)
            records.append(rec)
            if args.verbose:
                _print_record(rec)
    else:
        with ProcessPoolExecutor(max_workers=args.concurrency) as ex:
            future_to_dir = {ex.submit(rescore_task, td): td for td in task_dirs}
            for fut in as_completed(future_to_dir):
                rec = fut.result()
                records.append(rec)
                if args.verbose:
                    _print_record(rec)

    records.sort(key=lambda r: (r.get("domain", ""), r.get("task_id", "")))
    _print_summary(records)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        print(f"\nReport written to {args.output}")
    return 0


def _print_record(rec: dict) -> None:
    if rec.get("error"):
        print(f"[ERR ] {rec['domain']}/{rec['task_id']}: {rec['error']}")
        return
    orig = rec.get("original_score")
    rev = rec.get("revised_score")
    status = rec.get("status", "?")
    tag = {"complete": "OK  ", "incomplete_determined": "DET ",
           "incomplete_inconclusive": "INC "}.get(status, "?   ")
    if rev is not None and rev > 0 and status == "complete":
        tag = "FIX "
    rev_str = f"{rev:.3f}" if rev is not None else "None"
    print(f"[{tag}] {rec['domain']}/{rec['task_id']}: "
          f"orig={orig} -> revised={rev_str} ({status}, "
          f"scored={rec.get('num_scored')}/{rec.get('num_metrics')}, "
          f"rule_recomputed={rec.get('expected_recomputed')})")


def _print_summary(records: list[dict]) -> None:
    total = len(records)
    errors = [r for r in records if r.get("error")]
    ok = [r for r in records if not r.get("error")]
    complete = [r for r in ok if r.get("status") == "complete"]
    inconclusive = [r for r in ok if r.get("status") == "incomplete_inconclusive"]
    fixed = [r for r in complete if (r.get("original_score") or 0) == 0.0 and (r.get("revised_score") or 0) > 0.0]
    now_full = [r for r in complete if (r.get("revised_score") or 0) >= 1.0]
    regressed = [r for r in complete if (r.get("revised_score") or 0) < (r.get("original_score") or 0)]
    print("\n========== Summary ==========")
    print(f"Total revised tasks      : {total}")
    print(f"Errors                   : {len(errors)}")
    print(f"Scored OK                : {len(ok)}")
    print(f"  complete (all metrics) : {len(complete)}")
    print(f"  inconclusive (partial) : {len(inconclusive)}  <- needs full re-run to resolve")
    print(f"False-neg fixed          : {len(fixed)}  (orig==0 -> revised>0, complete)")
    print(f"Revised score == 1.0     : {len(now_full)}  (complete)")
    print(f"Regressed (rev<orig)     : {len(regressed)}")
    if errors:
        print("\nError samples:")
        for r in errors[:5]:
            print(f"  {r['domain']}/{r['task_id']}: {r['error']}")
    if regressed:
        print("\nRegression samples:")
        for r in regressed[:5]:
            print(f"  {r['domain']}/{r['task_id']}: {r.get('original_score')} -> {r.get('revised_score')}")
    if inconclusive:
        print("\nInconclusive samples (use full re-run script to resolve):")
        for r in inconclusive[:5]:
            print(f"  {r['domain']}/{r['task_id']}: scored={r.get('num_scored')}/{r.get('num_metrics')}")


if __name__ == "__main__":
    raise SystemExit(main())
