"""Review text cleaning and feature preparation."""

from __future__ import annotations

import re

import pandas as pd
from bs4 import BeautifulSoup


def _clean_text(text: object) -> str:
    """Remove HTML and normalize whitespace while preserving emoji."""
    raw = "" if pd.isna(text) else str(text)
    no_html = BeautifulSoup(raw, "html.parser").get_text(" ")
    no_breaks = re.sub(r"[\r\n\t]+", " ", no_html)
    return re.sub(r"\s+", " ", no_breaks).strip()


def clean_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """Clean Steam reviews and add analysis-friendly columns."""
    if df is None or df.empty:
        return pd.DataFrame(columns=list(getattr(df, "columns", [])) + [
            "review_clean",
            "sentiment",
            "playtime_hours",
            "created_date",
            "updated_date",
            "review_length",
        ])

    out = df.copy()
    out["review_clean"] = out.get("review", pd.Series(dtype=str)).apply(_clean_text)
    out = out[out["review_clean"].str.len() >= 5].copy()
    out["created_date"] = pd.to_datetime(out.get("timestamp_created"), unit="s", errors="coerce").dt.date
    out["updated_date"] = pd.to_datetime(out.get("timestamp_updated"), unit="s", errors="coerce").dt.date
    out["playtime_hours"] = pd.to_numeric(out.get("playtime_forever", 0), errors="coerce").fillna(0) / 60
    out["sentiment"] = out.get("voted_up", False).map(lambda value: "positive" if bool(value) else "negative")
    out["review_length"] = out["review_clean"].str.len()
    return out.reset_index(drop=True)
