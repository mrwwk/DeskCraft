"""Check whether tasks in calc/impr/writ already score full marks when the
*initial* (uploaded) file is evaluated against the gold file -- i.e. a no-op
agent would pass. This reuses each task's own per-task evaluator.py metric,
mirroring the offline replay in desktop_env/evaluators/artifacts.py.

NOTE: the real harness opens the file in LibreOffice and hits Ctrl+S before
evaluating, which can re-serialize the file / recompute cached formula values.
Here we compare the raw uploaded file directly, so a "full score" result is a
strong signal that the task is trivially satisfiable (answer leakage). A
non-full score does not 100% guarantee the LO-saved version also fails, but in
practice the two agree for these office-document metrics.
"""
from __future__ import annotations

import importlib.util
import json
import logging
import os
import sys
import traceback
from hashlib import sha256
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Tuple

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_DIR)  # so per-task evaluators can `import desktop_env`
logging.basicConfig(level=logging.WARNING)
logging.getLogger("desktopenv").setLevel(logging.WARNING)
EXAMPLES_DIR = os.path.join(PROJECT_DIR, "evaluation_examples", "examples_per_task")
DOMAINS = ["calc", "impr", "writ"]

_MODULE_CACHE: Dict[str, ModuleType] = {}


def load_module(path: str) -> ModuleType:
    cached = _MODULE_CACHE.get(path)
    if cached is not None:
        return cached
    name = f"init_eval_{sha256(path.encode()).hexdigest()[:16]}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    _MODULE_CACHE[path] = module
    # Per-task evaluators often reconfigure logging to DEBUG; keep output clean.
    logging.getLogger("desktopenv").setLevel(logging.WARNING)
    logging.getLogger().setLevel(logging.WARNING)
    return module


def find_initial_file(task: Dict[str, Any], result_vm_path: Optional[str]) -> Optional[str]:
    """Resolve the uploaded file that corresponds to the evaluated VM path."""
    upload_files: List[Tuple[str, str]] = []
    for step in task.get("config", []):
        if step.get("type") == "upload_file":
            for f in step.get("parameters", {}).get("files", []):
                upload_files.append((f.get("local_path", ""), f.get("path", "")))
    if not upload_files:
        # Interactive tasks often `download` the initial file at runtime.
        has_download = any(step.get("type") == "download" for step in task.get("config", []))
        if has_download:
            return ("DOWNLOAD", None)
        return None
    # Prefer the file whose VM path matches the evaluator result path.
    chosen = None
    for local, vm in upload_files:
        if result_vm_path and vm == result_vm_path:
            chosen = local
            break
    if not chosen:
        chosen = upload_files[0][0]
    if os.path.isabs(chosen):
        return chosen if os.path.exists(chosen) else None
    return os.path.join(PROJECT_DIR, chosen)


def resolve_expected(task_dir: str, expected_cfg: Any) -> Optional[str]:
    if expected_cfg is None:
        return None
    if isinstance(expected_cfg, dict):
        path = expected_cfg.get("path")
        if not path:
            return None
        if os.path.isabs(path):
            return path if os.path.exists(path) else None
        return os.path.join(task_dir, path)
    return None


def as_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def run_metric(func: Callable, result_path: str, expected_path: Optional[str], options: Any) -> float:
    opts = options if isinstance(options, dict) else {}
    try:
        if expected_path is not None:
            score = float(func(result_path, expected_path, **opts))
        else:
            score = float(func(result_path, **opts))
    except TypeError:
        # metric may not accept expected
        try:
            score = float(func(result_path, **opts))
        except Exception:
            raise
    return score


def evaluate_task(task_dir: str) -> Dict[str, Any]:
    task_path = os.path.join(task_dir, "task.json")
    with open(task_path) as f:
        task = json.load(f)
    ev = task.get("evaluator", {})
    func_names = as_list(ev.get("func"))
    if not func_names or func_names == ["infeasible"]:
        return {"skipped": "no func / infeasible"}

    eval_file = ev.get("file")
    if not eval_file:
        return {"skipped": "no per-task evaluator file"}
    eval_file_path = os.path.join(task_dir, eval_file) if not os.path.isabs(eval_file) else eval_file
    if not os.path.isfile(eval_file_path):
        return {"skipped": "evaluator file missing", "path": eval_file_path}
    module = load_module(eval_file_path)

    result_cfgs = as_list(ev.get("result"))
    expected_cfgs = as_list(ev.get("expected"))
    # Classify: only vm_file vs cache_file comparisons can be tested offline
    # with the initial uploaded file. Other getters (vm_command_line, rule,
    # vm_file_tree ...) require a running VM.
    result_types = [c.get("type") if isinstance(c, dict) else None for c in result_cfgs]
    expected_types = [c.get("type") if isinstance(c, dict) else None for c in expected_cfgs]
    is_file_cmp = (
        len(result_cfgs) > 0
        and all(rt in ("vm_file", None) for rt in result_types)
        and all(et in ("cache_file", None) for et in expected_types)
    )
    if not is_file_cmp:
        return {"skipped": f"non-file eval (result={result_types}, expected={expected_types})"}
    options_list = as_list(ev.get("options"))
    # If single func but options not list -> wrap
    if len(options_list) == 1 and not isinstance(ev.get("options"), list):
        options_list = [ev.get("options")] * len(func_names)
    elif not options_list:
        options_list = [None] * len(func_names)

    scores: List[Dict[str, Any]] = []
    for i, fname in enumerate(func_names):
        fn = getattr(module, fname, None)
        if fn is None:
            scores.append({"func": fname, "error": "func not found in module"})
            continue
        result_cfg = result_cfgs[i] if i < len(result_cfgs) else (result_cfgs[0] if result_cfgs else None)
        expected_cfg = expected_cfgs[i] if i < len(expected_cfgs) else (expected_cfgs[0] if expected_cfgs else None)
        result_vm_path = result_cfg.get("path") if isinstance(result_cfg, dict) else None
        gold_path = resolve_expected(task_dir, expected_cfg)
        entry: Dict[str, Any] = {"func": fname}
        init = find_initial_file(task, result_vm_path)
        if isinstance(init, tuple) and init and init[0] == "DOWNLOAD":
            entry["error"] = "needs VM (downloaded initial file, not in assets)"
            entry["gold"] = gold_path
            scores.append(entry)
            continue
        init_path = init
        if not init_path or not os.path.isfile(init_path):
            entry["error"] = f"initial file not found: {init_path}"
            entry["initial"] = init_path
            entry["gold"] = gold_path
            scores.append(entry)
            continue
        entry["initial"] = os.path.relpath(init_path, PROJECT_DIR)
        entry["gold"] = os.path.relpath(gold_path, PROJECT_DIR) if gold_path else None
        opts = options_list[i] if i < len(options_list) else None
        try:
            entry["score"] = run_metric(fn, init_path, gold_path, opts)
        except Exception as e:
            entry["error"] = f"{type(e).__name__}: {e}"
            entry["trace"] = traceback.format_exc(limit=2)
        scores.append(entry)

    # combine with conj (default and)
    conj = ev.get("conj", "and")
    numeric = [s.get("score") for s in scores if isinstance(s.get("score"), (int, float))]
    has_err = any("error" in s for s in scores)
    if numeric and not has_err:
        if conj == "or":
            total = 1.0 if any(v >= 1.0 for v in numeric) else 0.0
        else:
            total = 1.0 if all(v >= 1.0 for v in numeric) else (sum(numeric) / len(numeric) if numeric else 0.0)
    else:
        total = None
    return {"scores": scores, "conj": conj, "total": total}


def main() -> int:
    only_domains = sys.argv[1:] or DOMAINS
    print(f"Project: {PROJECT_DIR}")
    for domain in only_domains:
        ddir = os.path.join(EXAMPLES_DIR, domain)
        if not os.path.isdir(ddir):
            print(f"!! domain dir missing: {ddir}")
            continue
        tasks = sorted(os.listdir(ddir))
        print(f"\n########## {domain}  ({len(tasks)} tasks) ##########")
        full = []
        nonzero = []
        zero = []
        skipped = []
        errored = []
        for tname in tasks:
            tdir = os.path.join(ddir, tname)
            if not os.path.isdir(tdir):
                continue
            try:
                res = evaluate_task(tdir)
            except Exception as e:
                res = {"scores": [{"func": "?", "error": f"load fail: {type(e).__name__}: {e}"}], "conj": "and", "total": None}
            if "skipped" in res:
                skipped.append((tname, res["skipped"]))
                continue
            total = res.get("total")
            if total is None:
                errored.append((tname, res))
            elif total >= 1.0:
                full.append((tname, res))
            elif total > 0.0:
                nonzero.append((tname, total, res))
            else:
                zero.append((tname, res))

        print(f"\n--- {domain} summary ---")
        print(f"  FULL SCORE (initial == gold): {len(full)}")
        print(f"  partial (>0 <1):              {len(nonzero)}")
        print(f"  zero:                         {len(zero)}")
        print(f"  skipped:                      {len(skipped)}")
        print(f"  errored:                      {len(errored)}")

        if full:
            print(f"\n  *** FULL-SCORE (suspect answer leakage) ***")
            for tname, res in full:
                print(f"    [FULL] {domain}/{tname}")
                for s in res["scores"]:
                    print(f"        - {s.get('func')}: score={s.get('score')} {s.get('error','')}")
        if nonzero:
            print(f"\n  --- partial ---")
            for tname, total, res in nonzero:
                det = ",".join(f"{s.get('func')}={s.get('score')}" for s in res["scores"] if 'score' in s)
                print(f"    [PART {total:.3f}] {domain}/{tname}  {det}")
        if errored:
            print(f"\n  --- errored (need LO round-trip / VM) ---")
            for tname, res in errored[:10]:
                for s in res["scores"]:
                    if "error" in s:
                        print(f"    [ERR] {domain}/{tname} {s.get('func')}: {s.get('error')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
