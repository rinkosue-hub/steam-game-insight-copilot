"""Business tag classification and playtime-recommendation quadrant analysis."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from src.utils import PROJECT_ROOT


def load_tag_rules(path: str = "config/tag_rules.yaml") -> dict:
    """Load business tag keyword rules from YAML."""
    rule_path = Path(path)
    if not rule_path.is_absolute():
        rule_path = PROJECT_ROOT / rule_path
    with rule_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def classify_review(text: str, rules: dict) -> list[str]:
    """Classify one review into zero or more business tags."""
    content = (text or "").lower()
    tags: list[str] = []
    for tag, keywords in (rules or {}).items():
        if any(str(keyword).lower() in content for keyword in keywords):
            tags.append(tag)
    return tags


def classify_reviews(df: pd.DataFrame, rules: dict) -> pd.DataFrame:
    """Add a tags column to cleaned reviews."""
    out = df.copy() if df is not None else pd.DataFrame()
    if out.empty:
        out["tags"] = []
        return out
    text_col = "review_clean" if "review_clean" in out.columns else "review"
    out["tags"] = out[text_col].fillna("").apply(lambda text: classify_review(str(text), rules))
    return out


def tag_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize tag frequency, ratio, and representative examples."""
    if df is None or df.empty or "tags" not in df.columns:
        return pd.DataFrame(columns=["tag", "count", "ratio", "example_review"])
    exploded = df[df["tags"].map(bool)].explode("tags")
    if exploded.empty:
        return pd.DataFrame(columns=["tag", "count", "ratio", "example_review"])
    total = len(df)
    rows = []
    for tag, group in exploded.groupby("tags"):
        example = group.get("review_clean", group.get("review")).dropna().astype(str).iloc[0]
        rows.append({"tag": tag, "count": int(len(group)), "ratio": len(group) / total, "example_review": example})
    return pd.DataFrame(rows).sort_values("count", ascending=False).reset_index(drop=True)


def _quadrant(avg_playtime_hours: float, median_playtime_hours: float, recommendation_rate: float) -> str:
    """Map average playtime and recommendation rate to a business quadrant label."""
    if avg_playtime_hours >= median_playtime_hours and recommendation_rate >= 0.6:
        return "高粘性卖点"
    if avg_playtime_hours >= median_playtime_hours and recommendation_rate < 0.4:
        return "深度体验痛点"
    if avg_playtime_hours < median_playtime_hours and recommendation_rate >= 0.6:
        return "轻量正向体验"
    if avg_playtime_hours < median_playtime_hours and recommendation_rate < 0.4:
        return "早期流失风险"
    return "分歧反馈"


def build_quadrant_data(df: pd.DataFrame) -> pd.DataFrame:
    """Build playtime-recommendation quadrant data by business tag."""
    columns = [
        "tag",
        "count",
        "hotness",
        "hotness_percent",
        "avg_playtime_hours",
        "median_playtime_hours",
        "positive_count",
        "negative_count",
        "recommendation_rate",
        "sentiment_score",
        "quadrant",
        "example_review",
    ]
    if df is None or df.empty or "tags" not in df.columns:
        return pd.DataFrame(columns=columns)
    exploded = df[df["tags"].map(bool)].explode("tags")
    if exploded.empty:
        return pd.DataFrame(columns=columns)

    total_tag_count = len(exploded)
    rows = []
    for tag, group in exploded.groupby("tags"):
        count = len(group)
        positive = int((group["sentiment"] == "positive").sum()) if "sentiment" in group else 0
        negative = int((group["sentiment"] == "negative").sum()) if "sentiment" in group else 0
        hotness = count / total_tag_count if total_tag_count else 0
        recommendation_rate = positive / count if count else 0
        playtime = pd.to_numeric(group.get("playtime_hours", pd.Series([0])), errors="coerce").fillna(0)
        example = group.get("review_clean", group.get("review")).dropna().astype(str).iloc[0]
        rows.append(
            {
                "tag": tag,
                "count": int(count),
                "hotness": hotness,
                "hotness_percent": hotness * 100,
                "avg_playtime_hours": float(playtime.mean()),
                "median_playtime_hours": float(playtime.median()),
                "positive_count": positive,
                "negative_count": negative,
                "recommendation_rate": recommendation_rate,
                "sentiment_score": recommendation_rate,
                "example_review": example,
            }
        )

    result = pd.DataFrame(rows)
    median_playtime_hours = float(result["avg_playtime_hours"].median()) if not result.empty else 0
    result["quadrant"] = result.apply(
        lambda row: _quadrant(row["avg_playtime_hours"], median_playtime_hours, row["recommendation_rate"]),
        axis=1,
    )
    return result[columns].sort_values(["avg_playtime_hours", "recommendation_rate"], ascending=[False, False]).reset_index(drop=True)
