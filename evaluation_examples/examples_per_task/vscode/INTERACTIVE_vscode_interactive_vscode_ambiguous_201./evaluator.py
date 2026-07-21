import json
import re
import zipfile


def _normalize(path: str) -> str:
    return path.lstrip("./").replace("\\", "/")


def _read_text(zf: zipfile.ZipFile, raw_name: str) -> str:
    return zf.read(raw_name).decode("utf-8", errors="ignore")


def _find_tag(html: str, tag: str, element_id: str = None, class_name: str = None) -> bool:
    pattern = re.compile(rf"<{tag}\b[^>]*>", re.IGNORECASE)
    for match in pattern.finditer(html):
        tag_text = match.group(0)
        if element_id and not re.search(rf'\bid=["\']{re.escape(element_id)}["\']', tag_text, re.IGNORECASE):
            continue
        if class_name and not re.search(rf'\bclass=["\'][^"\']*\b{re.escape(class_name)}\b[^"\']*["\']', tag_text, re.IGNORECASE):
            continue
        return True
    return False


def check_b2b_landing_page_prototype(actual: str, expected=None, **options) -> float:
    if not actual:
        return 0.0

    try:
        with zipfile.ZipFile(actual, "r") as zf:
            name_map = {_normalize(name): name for name in zf.namelist()}
            for required in ("index.html", "styles.css", "manifest.json"):
                if required not in name_map:
                    return 0.0

            html = _read_text(zf, name_map["index.html"])
            manifest = json.loads(_read_text(zf, name_map["manifest.json"]))
    except Exception:
        return 0.0

    if not _find_tag(html, "main", element_id="app"):
        return 0.0
    if not _find_tag(html, "section", element_id="hero", class_name="hero"):
        return 0.0
    if not _find_tag(html, "section", element_id="proof", class_name="proof"):
        return 0.0
    if not re.search(r'<button[^>]*id=["\']cta["\'][^>]*>\s*Request Demo\s*</button>', html, re.IGNORECASE | re.DOTALL):
        return 0.0
    if "Orbit Analytics" not in html:
        return 0.0
    if len(re.findall(r'class=["\'][^"\']*\bproof-card\b[^"\']*["\']', html, re.IGNORECASE)) != 3:
        return 0.0

    if manifest.get("project") != "orbit-analytics":
        return 0.0
    if manifest.get("theme") != "midnight":
        return 0.0
    if str(manifest.get("version")) != "1.1":
        return 0.0

    return 1.0
