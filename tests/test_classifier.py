"""Tests for classifier."""

import pandas as pd

from src.classifier import classify_review, classify_reviews, tag_summary


RULES = {
    "玩法体验": ["玩法", "fun"],
    "BUG/崩溃": ["bug", "崩溃"],
    "美术/音乐": ["音乐"],
}


def test_classify_review_multiple_tags() -> None:
    """One review can match multiple tags."""
    tags = classify_review("玩法 fun 但是有 bug", RULES)
    assert "玩法体验" in tags
    assert "BUG/崩溃" in tags


def test_classify_reviews_adds_tags() -> None:
    """DataFrame classification should add tags column."""
    df = pd.DataFrame({"review_clean": ["玩法很爽", "音乐很好"]})
    out = classify_reviews(df, RULES)
    assert "tags" in out.columns
    assert out.loc[0, "tags"] == ["玩法体验"]


def test_tag_summary_outputs_count_ratio() -> None:
    """Tag summary should contain count and ratio."""
    df = pd.DataFrame(
        {
            "review_clean": ["玩法很爽", "音乐很好"],
            "tags": [["玩法体验"], ["美术/音乐"]],
        }
    )
    summary = tag_summary(df)
    assert {"count", "ratio"}.issubset(summary.columns)
    assert summary["count"].sum() == 2
