"""Shared utilities for Steam Game Insight Copilot."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional, Union


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def ensure_dir(path: Union[str, Path]) -> Path:
    """Create a directory if needed and return it as a Path."""
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def safe_filename(value: str) -> str:
    """Convert arbitrary text into a filesystem-friendly filename fragment."""
    cleaned = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", str(value).strip())
    return cleaned.strip("_") or "steam_game"


def first_error_message(result: Any) -> Optional[str]:
    """Return an error message stored on a DataFrame attrs object, if present."""
    attrs = getattr(result, "attrs", {}) or {}
    return attrs.get("error")
