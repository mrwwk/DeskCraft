def check_csv_summary_fix(actual_files, **options) -> float:
    """Check that the CSV summarizer bug is fixed and SUMMARY_FIXED.txt is created.

    actual_files: list of paths to files pulled from VM via vm_file multi=true.
    Expected order: [summarize.py_path, SUMMARY_FIXED.txt_path]

    Returns 1.0 only when both checks pass:
    - summarize.py contains 'next(reader)' (skips CSV header)
    - SUMMARY_FIXED.txt contains exactly 'csv summary fixed'
    """
    if not actual_files:
        return 0.0

    summarize_py = actual_files[0] if len(actual_files) > 0 else None
    summary_txt = actual_files[1] if len(actual_files) > 1 else None

    # Check 1: summarize.py must contain next(reader) to skip the CSV header
    if summarize_py is None:
        return 0.0
    try:
        with open(summarize_py, 'r') as f:
            content = f.read()
    except Exception:
        return 0.0

    if 'next(reader)' not in content:
        return 0.0

    # Check 2: SUMMARY_FIXED.txt must contain exactly 'csv summary fixed'
    if summary_txt is None:
        return 0.0
    try:
        with open(summary_txt, 'r') as f:
            content = f.read().strip()
    except Exception:
        return 0.0

    if content != 'csv summary fixed':
        return 0.0

    return 1.0
