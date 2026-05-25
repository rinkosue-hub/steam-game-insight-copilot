"""CSV, markdown, and zip export helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from src.utils import PROJECT_ROOT, ensure_dir, safe_filename


def _timestamp() -> str:
    """Return compact timestamp for exported filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_dataframe_csv(df: pd.DataFrame, filename_prefix: str) -> str:
    """Save a DataFrame to outputs/exports and return the path."""
    out_dir = ensure_dir(PROJECT_ROOT / "outputs" / "exports")
    path = out_dir / f"{safe_filename(filename_prefix)}_{_timestamp()}.csv"
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return str(path)


def save_markdown_report(report: str, filename_prefix: str) -> str:
    """Save a markdown report to outputs/reports and return the path."""
    out_dir = ensure_dir(PROJECT_ROOT / "outputs" / "reports")
    path = out_dir / f"{safe_filename(filename_prefix)}_{_timestamp()}.md"
    path.write_text(report, encoding="utf-8")
    return str(path)


def create_zip_export(files: list[str], zip_name: str) -> str:
    """Create a zip file containing exported CSV/Markdown artifacts."""
    out_dir = ensure_dir(PROJECT_ROOT / "outputs" / "exports")
    path = out_dir / f"{safe_filename(zip_name)}_{_timestamp()}.zip"
    with ZipFile(path, "w") as zip_file:
        for file in files:
            target = Path(file)
            if target.exists():
                zip_file.write(target, arcname=target.name)
    return str(path)
