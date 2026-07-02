#!/usr/bin/env python3
"""Patch DeskCraft runners to use the per-task task_loader helpers.

For each runner we:
  1. Ensure ``from desktop_env.evaluators.task_loader import resolve_task_config_path, load_task_config``
     is present.
  2. Replace inline path construction (``os.path.join(args.test_config_base_dir,
     f"examples/{domain}/{example_id}.json")`` and the ``{domain}/{example_id}.json``
     variant) with ``resolve_task_config_path(args.test_config_base_dir, domain, example_id)``.
  3. Replace ``with open(<cfg>, ...) as <h>: example = json.load(<h>)`` with
     ``example = load_task_config(<cfg>)``.
  4. Rewrite the bodies of existing ``build_config_file_path`` / ``resolve_config_file``
     helpers to delegate to ``resolve_task_config_path``.

Files that the patterns do not match are reported for manual review.
"""
from __future__ import annotations

import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

IMPORT_LINE = (
    "from desktop_env.evaluators.task_loader import "
    "resolve_task_config_path, load_task_config"
)

# (file path relative to REPO)
RUNNERS = [
    "runners/run.py",
    "runners/run_multienv.py",
    "runners/run_multienv_owl.py",
    "runners/run_multienv_uipath.py",
    "runners/run_multienv_uitars15_v1.py",
    "runners/run_multienv_mobileagent_v3.py",
    "runners/run_multienv_qwen3vl.py",
    "runners/run_multienv_aguvis.py",
    "runners/run_multienv_hosted_gbox.py",
    "runners/run_multienv_uitars.py",
    "runners/run_multienv_claude.py",
    "runners/run_multienv_opencua.py",
    "runners/run_multienv_uitars15_v2.py",
    "runners/run_multienv_interactive.py",
    "runners/run_multienv_dart_gui.py",
    "runners/run_multienv_mano.py",
    "runners/run_multienv_qwen25vl.py",
    "runners/run_multienv_openaicua.py",
    "runners/run_multienv_gta1.py",
    "runners/run_multienv_o3.py",
    "runners/run_multienv_agi.py",
    "runners/run_multienv_aworldguiagent.py",
    "runners/run_multienv_autoglm.py",
    "runners/run_multienv_qwen35vl.py",          # build_config_file_path helper
    "runners/run_multienv_evocua.py",             # resolve_config_file helper
    "runners/run_multienv_evocua_interactive.py", # resolve_config_file helper
    "runners/run_multienv_kimi_k25.py",           # resolve_config_file helper
    "runners/run_multienv_r3agentv3.py",          # resolve_config_file helper
    "runners/run_coact.py",                       # {domain}/{ex_id}.json
    "runners/run_multienv_autoglm_v.py",          # {domain}/{example_id}.json
    "runners/run_maestro.py",                     # special
    "mm_agents/maestro/osworld_run_maestro.py",   # special
    "mm_agents/maestro/maestro/snapshot_restorer.py",  # special
    "main.py",
    "quickstart_task.py",
]


def ensure_import(text: str) -> str:
    if IMPORT_LINE in text:
        return text
    # insert after the last existing desktop_env import, else after first import block
    lines = text.splitlines(keepends=True)
    insert_at = None
    for i, line in enumerate(lines):
        if line.startswith("from desktop_env") or line.startswith("import desktop_env"):
            insert_at = i + 1
    if insert_at is None:
        # fallback: after first 'import' or 'from' line group
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                insert_at = i + 1
                break
    if insert_at is None:
        insert_at = 0
    lines.insert(insert_at, IMPORT_LINE + "\n")
    return "".join(lines)


# --- pattern replacements -----------------------------------------------------

# Pattern A1: inline path with examples/ subdir (single or multi-line os.path.join)
RE_PATH_EXAMPLES = re.compile(
    r'config_file\s*=\s*os\.path\.join\(\s*'
    r'args\.test_config_base_dir,\s*'
    r'f"examples/\{domain\}/\{example_id\}\.json"\s*\)',
    re.MULTILINE | re.DOTALL,
)

# Pattern A2: inline path WITHOUT examples/ subdir ({domain}/{example_id}.json)
RE_PATH_PLAIN = re.compile(
    r'config_file\s*=\s*os\.path\.join\(\s*'
    r'args\.test_config_base_dir,\s*'
    r'f"\{domain\}/\{example_id\}\.json"\s*\)',
    re.MULTILINE | re.DOTALL,
)

# Pattern D (coact): cfg = os.path.join(args.test_config_base_dir, f"{domain}/{ex_id}.json")
RE_PATH_COACT = re.compile(
    r'cfg\s*=\s*os\.path\.join\(\s*'
    r'args\.test_config_base_dir,\s*'
    r'f"\{domain\}/\{ex_id\}\.json"\s*\)',
    re.MULTILINE | re.DOTALL,
)

# json.load block: with open(<cfgvar>, ...) as <h>:\n <spaces>example = json.load(<h>)
RE_LOAD = re.compile(
    r'with\s+open\(\s*(config_file|cfg|config_path|example_path)\s*,[^)]*\)\s*as\s+(\w+)\s*:\s*\n'
    r'\s*example\s*=\s*json\.load\(\s*\2\s*\)',
    re.MULTILINE | re.DOTALL,
)
RE_LOAD_VAR = re.compile(  # variant where the loaded var is `example` only
    r'with\s+open\(\s*(?P<cfg>config_file|cfg|config_path|example_path)\s*,[^)]*\)\s*as\s+(?P<h>\w+)\s*:\s*\n'
    r'\s*example\s*=\s*json\.load\(\s*(?P=h)\s*\)',
    re.MULTILINE | re.DOTALL,
)


def apply_replacements(text: str, fname: str) -> tuple[str, list[str]]:
    notes = []
    new = text

    # path construction replacements
    if RE_PATH_EXAMPLES.search(new):
        new = RE_PATH_EXAMPLES.sub(
            'config_file = resolve_task_config_path(args.test_config_base_dir, domain, example_id)',
            new,
        )
        notes.append("path(examples)→resolve_task_config_path")
    if RE_PATH_PLAIN.search(new):
        new = RE_PATH_PLAIN.sub(
            'config_file = resolve_task_config_path(args.test_config_base_dir, domain, example_id)',
            new,
        )
        notes.append("path(plain)→resolve_task_config_path")
    if RE_PATH_COACT.search(new):
        new = RE_PATH_COACT.sub(
            'cfg = resolve_task_config_path(args.test_config_base_dir, domain, ex_id)',
            new,
        )
        notes.append("cfg→resolve_task_config_path")

    # json.load block -> load_task_config
    def _load_sub(m):
        cfg = m.group(1)
        notes.append(f"load({cfg})→load_task_config")
        return f'example = load_task_config({cfg})'

    new = RE_LOAD.sub(_load_sub, new)

    return new, notes


def patch_helper_bodies(text: str, fname: str) -> tuple[str, list[str]]:
    """Rewrite build_config_file_path / resolve_config_file bodies to delegate."""
    notes = []

    # build_config_file_path(run_args, domain, example_id) -> resolve_task_config_path(run_args.test_config_base_dir, domain, example_id)
    pat_b = re.compile(
        r'(def\s+build_config_file_path\(\s*run_args\s*,\s*domain\s*,\s*example_id\s*\)\s*->\s*str:\s*\n)'
        r'(?:\s*"""[^"]*?"""\s*\n)?'
        r'\s*return\s+os\.path\.join\(\s*\n?\s*run_args\.test_config_base_dir,?\s*\n?'
        r'(?:\s*run_args\.examples_subdir,?\s*\n?)?'
        r'\s*domain,?\s*\n?\s*f"\{example_id\}\.json"\s*,?\s*\n?\s*\)',
        re.DOTALL,
    )
    if pat_b.search(text):
        text = pat_b.sub(
            r'\1    return resolve_task_config_path(run_args.test_config_base_dir, domain, example_id)',
            text,
        )
        notes.append("build_config_file_path→delegate")

    # resolve_config_file(test_config_base_dir, domain, example_id) -> resolve_task_config_path(...)
    # Replace the entire function body (from def line to next blank-line def or end of candidates)
    pat_c = re.compile(
        r'(def\s+resolve_config_file\(\s*test_config_base_dir\s*:\s*str\s*,\s*domain\s*:\s*str\s*,\s*example_id\s*:\s*str\s*\)\s*->\s*str:\s*\n)'
        r'(?:\s*"""[^"]*?"""\s*\n)?'
        r'(?:.*?\n)*?'
        r'\s*return\s+candidate_paths\[0\]|return\s+\w+\[0\]',
        re.DOTALL,
    )
    if pat_c.search(text):
        text = pat_c.sub(
            r'\1    return resolve_task_config_path(test_config_base_dir, domain, example_id)',
            text,
        )
        notes.append("resolve_config_file→delegate")

    return text, notes


def patch_main_quickstart(text: str, fname: str) -> tuple[str, list[str]]:
    """main.py / quickstart_task.py: wrap json.load with load_task_config."""
    notes = []
    # main.py: example_path = ...; with open(example_path,...) as f: example = json.load(f)
    m = re.search(
        r'(\s*with\s+open\(\s*example_path\s*,[^)]*\)\s*as\s+\w+\s*:\s*\n\s*)example\s*=\s*json\.load\(\s*\w+\s*\)',
        text,
    )
    if m:
        text = text[:m.start()] + text[m.start():m.end()].replace(
            m.group(0), m.group(1).rstrip() + "\n    example = load_task_config(example_path)"
        ) + text[m.end():]
        notes.append("main/qs load→load_task_config")
    return text, notes


def main() -> int:
    report = []
    for rel in RUNNERS:
        path = os.path.join(REPO, rel)
        if not os.path.isfile(path):
            report.append(f"MISSING: {rel}")
            continue
        with open(path, "r", encoding="utf-8") as f:
            orig = f.read()
        text = orig
        text = ensure_import(text)
        text, n1 = patch_helper_bodies(text, rel)
        text, n2 = apply_replacements(text, rel)
        text, n3 = patch_main_quickstart(text, rel)
        notes = n1 + n2 + n3
        changed = text != orig
        if changed:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            report.append(f"PATCHED  {rel}: {', '.join(notes) if notes else '(import only)'}")
        else:
            report.append(f"UNCHANGED {rel}")
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
