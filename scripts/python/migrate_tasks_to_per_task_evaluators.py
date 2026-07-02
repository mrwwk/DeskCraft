#!/usr/bin/env python3
"""Migrate flat task JSONs into per-task directories with self-contained evaluator.py.

For each task in ``evaluation_examples/ubuntu_examples/<domain>/<example_id>.json``
this creates ``evaluation_examples/examples_per_task/<domain>/<example_id>/``
containing:

* ``task.json``  - the original task JSON with ``evaluator.file = "evaluator.py"`` added
  (only when the per-task evaluator validated successfully; otherwise the field is
  omitted so the central ``desktop_env.evaluators.metrics`` registry is used as a
  fallback via ``loader.resolve_metric``).
* ``evaluator.py`` - a *self-contained* module containing the task's metric
  function(s) plus every helper, class and module-level constant it transitively
  references, extracted from ``desktop_env/evaluators/metrics/*.py`` via AST
  dependency tracing.

Original flat task files are left untouched (the repo is not under git, so all
output is additive under ``examples_per_task/``).

Exceptions that fall back to central metrics (no ``evaluator.file``):
  * ``func == "infeasible"`` (special-cased in DesktopEnv.evaluate, never dispatched)
  * ``func == "check_interactive_final_result"`` (dynamic delegator over the whole
    metrics registry; cannot be made self-contained)
  * any ``func`` not found in the exported metrics namespace
  * extraction that fails validation (syntax / func not defined / unresolved names)
  * a name collision across two modules in the dependency closure
"""
from __future__ import annotations

import ast
import builtins
import json
import os
import sys
import textwrap
from typing import Any, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
METRICS_DIR = os.path.join(REPO_DIR, "desktop_env", "evaluators", "metrics")
METRICS_INIT = os.path.join(METRICS_DIR, "__init__.py")
TASKS_SRC_DIR = os.path.join(REPO_DIR, "evaluation_examples", "ubuntu_examples")
OUT_DIR = os.path.join(REPO_DIR, "evaluation_examples", "examples_per_task")

BUILTINS: Set[str] = set(dir(builtins)) | {"__name__", "__file__"}

# Funcs that must never be split out (use central-metrics fallback).
SKIP_FUNCS: Set[str] = {"infeasible", "check_interactive_final_result"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def seg(source: str, node: ast.AST) -> str:
    """Return the source segment for *node*, preserving original formatting."""
    s = ast.get_source_segment(source, node)
    if s is None:
        lines = source.splitlines()
        s = "\n".join(lines[node.lineno - 1: node.end_lineno])
    return textwrap.dedent(s)


def resolve_import_origin(node: ast.ImportFrom) -> Tuple[str, Optional[str], List[Tuple[str, Optional[str]]]]:
    """Classify an ImportFrom node.

    Returns ``(kind, module_name, entries)`` where ``kind`` is one of:
      * ``"intra-name"``   - relative import or absolute import from
        ``desktop_env.evaluators.metrics.<mod>``; ``entries`` is
        ``[(local_name, original_name), ...]``.
      * ``"intra-module"`` - ``from desktop_env.evaluators.metrics import <mod> as <alias>``;
        ``entries`` is ``[(local_name, module_name), ...]``.
      * ``"external"``      - any other import; ``entries`` is unused.
    """
    module = node.module or ""
    # relative import (from .X import ...) -> always intra-metrics
    if node.level and node.level > 0:
        mod = module
        entries = [(a.asname or a.name, a.name) for a in node.names]
        return ("intra-name", mod, entries)
    # absolute intra: desktop_env.evaluators.metrics[.<mod>]
    if module == "desktop_env.evaluators.metrics":
        # from desktop_env.evaluators.metrics import <mod> [as alias]  (module import)
        entries = [(a.asname or a.name, a.name) for a in node.names]
        return ("intra-module", None, entries)
    if module.startswith("desktop_env.evaluators.metrics."):
        mod = module.split(".")[-1]
        entries = [(a.asname or a.name, a.name) for a in node.names]
        return ("intra-name", mod, entries)
    return ("external", None, [])


# ---------------------------------------------------------------------------
# Module index
# ---------------------------------------------------------------------------
class ModuleInfo:
    def __init__(self, name: str, path: str, source: str, tree: ast.Module):
        self.name = name
        self.path = path
        self.source = source
        self.tree = tree
        self.defs: Dict[str, ast.AST] = {}          # name -> FunctionDef/AsyncFunctionDef/ClassDef
        self.consts: Dict[str, ast.AST] = {}        # name -> Assign/AnnAssign
        self.external_imports: List[str] = []       # source segments
        self.intra_imports: Dict[str, Tuple[str, Optional[str]]] = {}
        # local_name -> (origin_module, origin_name); origin_name None = module import

    def is_logger_assign(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if isinstance(t, ast.Name) and t.id == "logger":
                v = node.value
                if isinstance(v, ast.Call):
                    f = v.func
                    if (isinstance(f, ast.Attribute) and f.attr == "getLogger") or \
                       (isinstance(f, ast.Name) and f.id == "getLogger"):
                        return True
        return False


def parse_module(name: str, path: str) -> ModuleInfo:
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source)
    mi = ModuleInfo(name, path, source, tree)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            mi.defs[node.name] = node
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    if mi.is_logger_assign(node):
                        continue  # skip module logger; we emit our own
                    mi.consts[t.id] = node
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                mi.consts[node.target.id] = node
        elif isinstance(node, ast.Import):
            mi.external_imports.append(seg(source, node))
        elif isinstance(node, ast.ImportFrom):
            kind, mod, entries = resolve_import_origin(node)
            if kind == "intra-name":
                for local, oname in entries:
                    mi.intra_imports[local] = (mod, oname)
            elif kind == "intra-module":
                for local, m in entries:
                    mi.intra_imports[local] = (m, None)
            else:
                mi.external_imports.append(seg(source, node))
    return mi


def load_all_modules() -> Dict[str, ModuleInfo]:
    mods: Dict[str, ModuleInfo] = {}
    for fname in sorted(os.listdir(METRICS_DIR)):
        if not fname.endswith(".py") or fname == "__init__.py":
            continue
        name = fname[:-3]
        mods[name] = parse_module(name, os.path.join(METRICS_DIR, fname))
    return mods


def build_exported_map() -> Dict[str, Tuple[str, str]]:
    """Parse metrics/__init__.py -> {exported_name: (module, original_name)}."""
    with open(METRICS_INIT, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source)
    out: Dict[str, Tuple[str, str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        if not node.level:  # only relative imports (from .X import ...) are the re-exports
            continue
        mod = node.module or ""
        for a in node.names:
            exported = a.asname or a.name
            out[exported] = (mod, a.name)
    return out


# ---------------------------------------------------------------------------
# Dependency tracing
# ---------------------------------------------------------------------------
def local_names_of(func_node: ast.AST) -> Set[str]:
    """Names bound locally inside a function body (params, assigns, nested defs, ...).

    Includes nested ``def``/``class`` names and the locals of nested functions so
    that closures (a helper that defines an inner ``def`` and calls it) are not
    flagged as unresolved. This is deliberately permissive: a referenced name is
    only reported as unresolved if it is neither top-level, nor a builtin, nor
    bound anywhere within the function's scope tree.
    """
    locals_: Set[str] = set()
    # function args
    if isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        args = func_node.args
        for a in list(args.args) + list(args.posonlyargs) + list(args.kwonlyargs):
            locals_.add(a.arg)
        if args.vararg:
            locals_.add(args.vararg.arg)
        if args.kwarg:
            locals_.add(args.kwarg.arg)
    for n in ast.walk(func_node):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            locals_.add(n.id)
        elif isinstance(n, ast.arg):
            locals_.add(n.arg)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            locals_.add(n.name)
        elif isinstance(n, ast.Global):
            locals_.update(n.names)  # these refer to module globals (available)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                locals_.add(a.asname or a.name.split(".")[0])
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # nested def/class names are bound in the enclosing scope (closures)
            locals_.add(n.name)
    return locals_


def referenced_load_names(node: ast.AST) -> Set[str]:
    return {n.id for n in ast.walk(node)
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def trace_closure(
    func_specs: List[Tuple[str, str]],
    modules: Dict[str, ModuleInfo],
) -> Tuple[Set[Tuple[str, str]], Set[Tuple[str, str]], List[str], bool]:
    """BFS over the dependency closure starting from *func_specs*.

    Returns ``(funcs_needed, consts_needed, touched_modules, collision)``.
    *collision* is True if the same name would be emitted from two different
    modules (caller should fall back to central metrics).
    """
    funcs_needed: Set[Tuple[str, str]] = set()
    consts_needed: Set[Tuple[str, str]] = set()
    touched: Set[str] = set()
    visited: Set[Tuple[str, str, str]] = set()

    queue: List[Tuple[str, str, str]] = [(m, n, "func") for (m, n) in func_specs]
    while queue:
        mod, name, kind = queue.pop()
        if (mod, name, kind) in visited:
            continue
        visited.add((mod, name, kind))

        mi = modules.get(mod)
        if mi is None:
            continue

        if kind == "func":
            node = mi.defs.get(name)
            if node is None:
                # maybe intra-imported name -> trace to origin
                if name in mi.intra_imports:
                    om, on = mi.intra_imports[name]
                    if on is not None:
                        queue.append((om, on, "func"))
                continue
            funcs_needed.add((mod, name))
            touched.add(mod)
        else:  # const
            node = mi.consts.get(name)
            if node is None:
                if name in mi.intra_imports:
                    om, on = mi.intra_imports[name]
                    if on is not None:
                        queue.append((om, on, "func"))  # const may reference a func
                continue
            consts_needed.add((mod, name))
            touched.add(mod)

        # collect referenced Load names -> resolve within this module
        for ref in referenced_load_names(node):
            if ref in mi.defs:
                queue.append((mod, ref, "func"))
            elif ref in mi.intra_imports:
                om, on = mi.intra_imports[ref]
                if on is not None:
                    queue.append((om, on, "func"))
                # module imports (on is None) cannot be inlined -> caller will detect
            elif ref in mi.consts:
                queue.append((mod, ref, "const"))
            # else: external/builtin -> ignored (handled by import block / builtins)

    # collision detection: same name emitted from two modules
    name_to_mod: Dict[str, str] = {}
    collision = False
    for (mod, name) in funcs_needed:
        if name in name_to_mod and name_to_mod[name] != mod:
            collision = True
            break
        name_to_mod[name] = mod
    if not collision:
        for (mod, name) in consts_needed:
            if name in name_to_mod and name_to_mod[name] != mod:
                collision = True
                break
            name_to_mod[name] = mod
    # also: a func and a const sharing a name is impossible (namespace), skip

    return funcs_needed, consts_needed, sorted(touched), collision


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def topo_sort_funcs(
    funcs_needed: Set[Tuple[str, str]],
    modules: Dict[str, ModuleInfo],
) -> List[Tuple[str, str]]:
    """Topologically sort funcs so callees precede callers (best effort)."""
    deps: Dict[Tuple[str, str], Set[Tuple[str, str]]] = {fn: set() for fn in funcs_needed}
    funcset = funcs_needed
    for (mod, name) in funcs_needed:
        mi = modules.get(mod)
        if mi is None or name not in mi.defs:
            continue
        node = mi.defs[name]
        for ref in referenced_load_names(node):
            target: Optional[Tuple[str, str]] = None
            if ref in mi.defs and (mod, ref) in funcset and ref != name:
                target = (mod, ref)
            elif ref in mi.intra_imports:
                om, on = mi.intra_imports[ref]
                if on is not None and (om, on) in funcset:
                    target = (om, on)
            if target and target != (mod, name):
                deps[(mod, name)].add(target)
    # Kahn's algorithm
    result: List[Tuple[str, str]] = []
    indeg = {fn: 0 for fn in funcs_needed}
    rev: Dict[Tuple[str, str], List[Tuple[str, str]]] = {fn: [] for fn in funcs_needed}
    for fn, ds in deps.items():
        for d in ds:
            if d in indeg:
                indeg[fn] += 1
                rev[d].append(fn)
    # deterministic order: sort by (module, name)
    ready = sorted([fn for fn in funcs_needed if indeg[fn] == 0])
    while ready:
        fn = ready.pop(0)
        result.append(fn)
        for nxt in rev[fn]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                # insert keeping deterministic order
                ready.append(nxt)
        ready.sort()
    # any remaining (cycles) appended
    for fn in sorted(funcs_needed):
        if fn not in result:
            result.append(fn)
    return result


def collect_alias_bindings(
    funcs_needed: Set[Tuple[str, str]],
    consts_needed: Set[Tuple[str, str]],
    touched: List[str],
    modules: Dict[str, ModuleInfo],
) -> List[str]:
    """Emit ``local = original`` alias lines for aliased intra-imports whose
    origin is in the closure (so the caller's local alias resolves)."""
    needed_names = {n for (_, n) in funcs_needed} | {n for (_, n) in consts_needed}
    lines: List[str] = []
    seen: Set[str] = set()
    for mod in touched:
        mi = modules.get(mod)
        if mi is None:
            continue
        for local, (om, on) in mi.intra_imports.items():
            if on is None:
                continue  # module import (interactive only); skip
            if on not in needed_names:
                continue
            if local == on:
                continue  # no alias needed; the def is emitted under `on`
            key = f"{local}={on}"
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"{local} = {on}")
    return lines


def assemble_evaluator(
    example_id: str,
    domain: str,
    func_names: List[str],
    funcs_needed: Set[Tuple[str, str]],
    consts_needed: Set[Tuple[str, str]],
    touched: List[str],
    modules: Dict[str, ModuleInfo],
) -> str:
    # imports: dedup union of external imports across touched modules
    import_lines: List[str] = []
    seen_imp: Set[str] = set()
    for mod in touched:
        mi = modules.get(mod)
        if mi is None:
            continue
        for imp in mi.external_imports:
            if imp not in seen_imp:
                seen_imp.add(imp)
                import_lines.append(imp)

    # Emit each touched module's needed constants AND functions interleaved in
    # source order (by line number). The original module compiles, so source
    # order is valid for within-module import-time dependencies (e.g. a
    # module-level constant that references another constant / function defined
    # earlier). Emitting in alphabetical order would break such chains.
    module_blocks: List[str] = []
    for mod in touched:
        mi = modules.get(mod)
        if mi is None:
            continue
        items: List[Tuple[int, str]] = []
        for (cm, cname) in consts_needed:
            if cm == mod and cname in mi.consts:
                node = mi.consts[cname]
                items.append((node.lineno, seg(mi.source, node)))
        for (fm, fname) in funcs_needed:
            if fm == mod and fname in mi.defs:
                node = mi.defs[fname]
                items.append((node.lineno, seg(mi.source, node)))
        items.sort(key=lambda x: x[0])
        if items:
            module_blocks.append("\n\n\n".join(text for _, text in items))

    alias_lines = collect_alias_bindings(funcs_needed, consts_needed, touched, modules)

    provenance = sorted({mod for mod in touched})
    header = (
        f'"""Per-task evaluator for {example_id}."""\n\n'
        f"# Generated by scripts/python/migrate_tasks_to_per_task_evaluators.py.\n"
        f"# Source modules: {', '.join('desktop_env/evaluators/metrics/' + m + '.py' for m in provenance)}\n"
    )
    logger_line = f'logger = logging.getLogger("desktopenv.metrics.{domain}")'

    parts = [header]
    if import_lines:
        parts.append("\n".join(import_lines))
    parts.append("import logging")
    parts.append(logger_line)
    if module_blocks:
        parts.append("\n\n\n".join(module_blocks))
    if alias_lines:
        parts.append("\n".join(alias_lines))

    body = "\n\n\n".join(parts) + "\n"
    return body


# ---------------------------------------------------------------------------
# Validation (static, no imports)
# ---------------------------------------------------------------------------
def validate_evaluator(
    evaluator_path: str,
    func_names: List[str],
) -> Tuple[bool, str]:
    with open(evaluator_path, "r", encoding="utf-8") as f:
        source = f.read()
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return False, f"syntax error: {e}"
    # top-level names defined/imported
    top_names: Set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            top_names.add(node.name)
            if node.name not in func_names:
                # a helper def - fine
                pass
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    top_names.add(t.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            top_names.add(node.target.id)
        elif isinstance(node, ast.Import):
            for a in node.names:
                top_names.add(a.asname or a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for a in node.names:
                top_names.add(a.asname or a.name)
    # every requested func must be a top-level def/class
    for fn in func_names:
        if fn not in top_names:
            return False, f"func '{fn}' not defined at top level"
    # unresolved-name check: every Load Name in each func must resolve
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        locals_ = local_names_of(node)
        available = top_names | BUILTINS | locals_
        for n in ast.walk(node):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                if n.id not in available:
                    return False, f"unresolved name '{n.id}' in '{node.name}'"
    return True, ""


def import_validate(
    evaluator_path: str,
    func_names: List[str],
) -> Tuple[bool, str]:
    """Load the evaluator module by path and confirm each func is callable.

    This is the authoritative check: it executes module-level code, so it catches
    import-time NameErrors (e.g. a constant referencing a not-yet-defined name),
    missing helpers, and any other runtime issue that the static check could
    miss. An ``ImportError`` is treated as a missing third-party dependency
    (present at runtime, absent in this validation environment) and does NOT
    cause a fallback.
    """
    import hashlib
    import importlib.util
    import sys

    digest = hashlib.sha256(evaluator_path.encode("utf-8")).hexdigest()[:16]
    mod_name = f"_migration_validate_{digest}"
    spec = importlib.util.spec_from_file_location(mod_name, evaluator_path)
    if spec is None or spec.loader is None:
        return False, "could not create import spec"
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    try:
        spec.loader.exec_module(module)
    except ImportError as e:
        # Assume a missing third-party dep that exists in the runtime env.
        return True, f"(skipped import error: {e})"
    except Exception as e:  # noqa: BLE001
        sys.modules.pop(mod_name, None)
        return False, f"import-time error: {type(e).__name__}: {e}"
    for fn in func_names:
        obj = getattr(module, fn, None)
        if not callable(obj):
            sys.modules.pop(mod_name, None)
            return False, f"func '{fn}' not callable after import"
    return True, ""


# ---------------------------------------------------------------------------
# Per-task processing
# ---------------------------------------------------------------------------
def process_task(
    domain: str,
    example_id: str,
    src_path: str,
    modules: Dict[str, ModuleInfo],
    exported: Dict[str, Tuple[str, str]],
) -> Tuple[str, str]:
    """Process one task. Returns (status, detail).

    status in {"generated", "fallback", "error"}.
    """
    with open(src_path, "r", encoding="utf-8") as f:
        task = json.load(f)

    evaluator = task.get("evaluator")
    if not isinstance(evaluator, dict):
        return ("fallback", "no evaluator block")
    func = evaluator.get("func")
    if isinstance(func, list):
        func_names = func
    elif isinstance(func, str):
        func_names = [func]
    else:
        return ("fallback", "no func")

    # skip rules
    for fn in func_names:
        if fn in SKIP_FUNCS:
            return ("fallback", f"skip func {fn}")
        if fn not in exported:
            return ("fallback", f"func {fn} not in exported metrics map")

    # resolve each func to (module, original_name)
    func_specs: List[Tuple[str, str]] = []
    for fn in func_names:
        mod, orig = exported[fn]
        func_specs.append((mod, orig))

    # trace closure
    funcs_needed, consts_needed, touched, collision = trace_closure(func_specs, modules)
    if collision:
        return ("fallback", "name collision across modules in closure")

    # check all needed funcs/consts resolve to actual defs (not dangling intra-imports)
    for (mod, name) in funcs_needed:
        mi = modules.get(mod)
        if mi is None or name not in mi.defs:
            return ("fallback", f"func {mod}.{name} not defined (dangling import?)")

    # assemble
    evaluator_src = assemble_evaluator(
        example_id, domain, func_names, funcs_needed, consts_needed, touched, modules
    )

    # write outputs
    out_dir = os.path.join(OUT_DIR, domain, example_id)
    os.makedirs(out_dir, exist_ok=True)
    ev_path = os.path.join(out_dir, "evaluator.py")
    with open(ev_path, "w", encoding="utf-8") as f:
        f.write(evaluator_src)

    # validate: static check then authoritative import check
    ok, msg = validate_evaluator(ev_path, func_names)
    if ok:
        ok, imp_msg = import_validate(ev_path, func_names)
        if not ok:
            msg = imp_msg
    if not ok:
        # Keep evaluator.py on disk for inspection, but omit ``file`` from task.json
        # so the loader falls back to central metrics (the per-task file is unused).
        tj_path = os.path.join(out_dir, "task.json")
        with open(tj_path, "w", encoding="utf-8") as f:
            json.dump(task, f, indent=2, ensure_ascii=False)
        return ("fallback", f"validation failed: {msg}")

    # success: write task.json with evaluator.file
    task_with_file = json.loads(json.dumps(task))  # deepcopy
    task_with_file.pop("_task_config_path", None)  # never persist the synthetic key
    task_with_file.setdefault("evaluator", {})["file"] = "evaluator.py"
    tj_path = os.path.join(out_dir, "task.json")
    with open(tj_path, "w", encoding="utf-8") as f:
        json.dump(task_with_file, f, indent=2, ensure_ascii=False)
    return ("generated", f"funcs={func_names} modules={touched}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    if not os.path.isdir(TASKS_SRC_DIR):
        print(f"ERROR: tasks source dir not found: {TASKS_SRC_DIR}", file=sys.stderr)
        return 1
    print("Loading metrics modules ...")
    modules = load_all_modules()
    print(f"  parsed {len(modules)} modules")
    exported = build_exported_map()
    print(f"  exported map has {len(exported)} names")

    # Output dir is overwritten per-task (idempotent re-runs). We intentionally do
    # NOT shutil.rmtree the output dir: a safe-delete guard blocks bulk deletes,
    # and overwriting individual files is sufficient. Stale evaluator.py files for
    # tasks that switched to fallback are harmless (task.json omits ``file``, so
    # the loader falls back to central metrics and ignores the stale file).
    os.makedirs(OUT_DIR, exist_ok=True)

    stats = {"generated": 0, "fallback": 0, "error": 0}
    fallbacks: List[str] = []
    n = 0
    domains = sorted(os.listdir(TASKS_SRC_DIR))
    for domain in domains:
        dom_dir = os.path.join(TASKS_SRC_DIR, domain)
        if not os.path.isdir(dom_dir):
            continue
        for fname in sorted(os.listdir(dom_dir)):
            if not fname.endswith(".json"):
                continue
            example_id = fname[:-4]
            src_path = os.path.join(dom_dir, fname)
            try:
                status, detail = process_task(domain, example_id, src_path, modules, exported)
            except Exception as e:  # noqa: BLE001
                status, detail = "error", f"{type(e).__name__}: {e}"
            stats[status] += 1
            n += 1
            if status != "generated":
                fallbacks.append(f"[{status}] {domain}/{example_id}: {detail}")
            if n % 50 == 0:
                print(f"  ...processed {n} tasks")

    print("\n=== Migration summary ===")
    print(f"  total:     {n}")
    print(f"  generated: {stats['generated']}")
    print(f"  fallback:  {stats['fallback']}")
    print(f"  error:     {stats['error']}")
    if fallbacks:
        print(f"\n--- fallback/error list ({len(fallbacks)}) ---")
        for line in fallbacks:
            print("  " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
