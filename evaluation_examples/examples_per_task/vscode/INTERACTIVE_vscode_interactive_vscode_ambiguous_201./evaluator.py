# Revised evaluator for interactive_vscode_ambiguous_201 Phase 1
# Task instruction: "帮我先做一个看起来像 B2B 产品首屏的页面原型。"
# This evaluator checks that the zip bundle contains a valid B2B landing page
# prototype HTML file, without requiring specific brand names, CSS selectors,
# or auxiliary files (styles.css, manifest.json) that Phase 1 never mentioned.
import json
import re
import zipfile
from typing import Any, Dict


def _normalize_ui_bundle_path(path: str) -> str:
    return path.lstrip("./").replace("\\", "/")


def check_b2b_landing_page_prototype(actual: str, expected=None, **options) -> float:
    """Check if the zip bundle contains a valid B2B product landing page prototype.

    Checks performed:
    1. Zip file exists and can be opened
    2. Contains at least one .html/.htm file (preferably index.html)
    3. HTML file has non-trivial content (>= 200 bytes after strip)
    4. HTML content contains B2B landing page indicators (nav, hero, CTA, etc.)

    Does NOT require: styles.css, manifest.json, specific brand names,
    specific CSS selectors/IDs, or manifest structure.
    """
    if not actual:
        return 0.0

    try:
        with zipfile.ZipFile(actual, "r") as zf:
            names = set(zf.namelist())
            normalized = {_normalize_ui_bundle_path(n) for n in names}

            # Find HTML files (exclude directory entries)
            html_files = [
                n for n in normalized
                if n.lower().endswith((".html", ".htm")) and n != ""
            ]
            if not html_files:
                return 0.0

            # Prefer index.html, otherwise use first HTML file found
            html_name = None
            for hf in html_files:
                if hf.lower().endswith("index.html") or hf.lower().endswith("index.htm"):
                    html_name = hf
                    break
            if html_name is None:
                html_name = html_files[0]

            # Get raw zip name and read content
            raw_name = next(n for n in names if _normalize_ui_bundle_path(n) == html_name)
            html_content = zf.read(raw_name).decode("utf-8", errors="ignore")

            content_stripped = html_content.strip()
            content_lower = html_content.lower()

            # Check 1: Non-trivial content (not empty/tiny)
            if len(content_stripped) < 200:
                return 0.0

            # Check 2: Has basic HTML document structure
            # Either a doctype/html tag or a body tag should be present
            has_doctype = "<!doctype" in content_lower
            has_html_tag = "<html" in content_lower
            has_body = "<body" in content_lower
            has_head = "<head" in content_lower or "<title" in content_lower

            if not (has_doctype or has_html_tag or has_body):
                # Allow minimal structure: at least has a body or html wrapper
                return 0.0

            # Check 3: Has B2B landing page characteristics
            # A B2B landing page typically has:
            # - Navigation elements
            # - Hero/main section
            # - Call-to-action elements
            # - Business/product-related content
            b2b_indicators = [
                # CTA / conversion elements
                "button", "sign up", "signup", "demo", "trial",
                "get started", "contact", "learn more", "subscribe",
                "cta", "request", "pricing", "free", "download",
                "try", "register", "join",
                # Navigation / layout
                "nav", "navbar", "menu", "header", "footer",
                # Section markers
                "hero", "section", "banner", "headline", "feature",
                "testimonial", "grid", "container", "wrapper",
                # B2B / business content
                "solution", "product", "service", "enterprise",
                "business", "platform", "analytics", "dashboard",
                "integration", "workflow", "automation", "scale",
                "team", "client", "partner", "customer",
                # Common B2B value props
                "trusted", "secure", "reliable", "fast", "easy",
                "powerful", "simple", "modern", "grow", "boost",
            ]

            indicator_count = sum(1 for ind in b2b_indicators if ind in content_lower)

            # A valid B2B landing page should contain at least 3 indicators
            # from different categories (e.g., nav + hero + cta = minimum)
            if indicator_count < 3:
                return 0.0

    except Exception:
        return 0.0

    return 1.0
