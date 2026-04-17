#!/usr/bin/env python3

"""Generate desktop_env.evaluators.metrics.__init__ exports.

This script imports every top-level function defined in the metrics package.
If the same function name appears in multiple modules, later imports would
overwrite earlier ones, so duplicates are exported as `<name>_<module>`.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
METRICS_DIR = REPO_ROOT / "desktop_env" / "evaluators" / "metrics"
INIT_FILE = METRICS_DIR / "__init__.py"


def iter_module_functions(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: list[str] = []
    seen: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name not in seen:
            names.append(node.name)
            seen.add(node.name)
    return names


def build_exports() -> tuple[dict[str, list[tuple[str, str]]], dict[str, list[str]]]:
    module_functions: dict[str, list[str]] = {}
    collisions: dict[str, list[str]] = defaultdict(list)

    for path in sorted(METRICS_DIR.glob("*.py"), key=lambda item: item.name.lower()):
        if path.name == "__init__.py":
            continue
        module_name = path.stem
        function_names = iter_module_functions(path)
        module_functions[module_name] = function_names
        for function_name in function_names:
            collisions[function_name].append(module_name)

    exports: dict[str, list[tuple[str, str]]] = {}
    for module_name, function_names in module_functions.items():
        module_exports: list[tuple[str, str]] = []
        for function_name in function_names:
            modules = collisions[function_name]
            export_name = function_name if len(modules) == 1 else f"{function_name}_{module_name}"
            module_exports.append((function_name, export_name))
        exports[module_name] = module_exports

    duplicate_map = {name: mods for name, mods in collisions.items() if len(mods) > 1}
    return exports, duplicate_map


def render_init(exports: dict[str, list[tuple[str, str]]], duplicate_map: dict[str, list[str]]) -> str:
    lines: list[str] = [
        '"""Auto-generated exports for metrics evaluators.',
        '',
        'Run `python scripts/python/generate_metrics_init.py` after adding or',
        'renaming functions in `desktop_env/evaluators/metrics/`.',
        '"""',
        '',
    ]

    if duplicate_map:
        lines.extend([
            "# Duplicate function names are exported with a module suffix to avoid collisions.",
            "",
        ])

    for module_name, module_exports in exports.items():
        lines.append(f"from .{module_name} import (")
        for function_name, export_name in module_exports:
            if function_name == export_name:
                lines.append(f"    {function_name},")
            else:
                lines.append(f"    {function_name} as {export_name},")
        lines.append(")")
        lines.append("")

    all_exports = [export_name for module_exports in exports.values() for _, export_name in module_exports]
    lines.append("__all__ = [")
    for export_name in all_exports:
        lines.append(f'    "{export_name}",')
    lines.append("]")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    exports, duplicate_map = build_exports()
    INIT_FILE.write_text(render_init(exports, duplicate_map), encoding="utf-8")


if __name__ == "__main__":
    main()
