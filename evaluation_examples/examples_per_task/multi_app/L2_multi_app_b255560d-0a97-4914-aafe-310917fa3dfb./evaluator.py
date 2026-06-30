"""
Evaluator for package_metadata_refresh_from_npm_handoff task.

Checks:
  1. check_json: package.json content matches HANDOFF.json (name, description,
     repository.url, homepage)
  2. check_include_exclude: README.md mentions the new package name @acme/widget-lib
  3. check_include_exclude: package.json.bak backup file exists in project directory

All three metrics come from the framework's general.py; this module re-exports them
so the framework can load them via evaluator.file = "evaluator.py".
"""
from desktop_env.evaluators.metrics.general import check_json, check_include_exclude
