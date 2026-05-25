"""Tests for quadrant builder."""

import pandas as pd

from src.classifier import build_quadrant_data


def test_build_quadrant_data_columns() -> None:
    """Quadrant data should include expected fields."""
    df = pd.DataFrame(
        {
            "review_clean": ["玩法爽", "玩法差", "音乐好", "bug多"],
            "sentiment": ["positive", "negative", "positive", "negative"],
            "tags": [["玩法体验"], ["玩法体验"], ["美术/音乐"], ["BUG/崩溃"]],
        }
    )
    out = build_quadrant_data(df)
    expected = {"tag", "count", "hotness", "hotness_percent", "sentiment_score", "quadrant"}
    assert expected.issubset(out.columns)
    assert not out.empty


def test_build_quadrant_data_empty_tags() -> None:
    """Empty tags should not raise and should return empty DataFrame."""
    df = pd.DataFrame({"review_clean": ["abc"], "sentiment": ["positive"], "tags": [[]]})
    out = build_quadrant_data(df)
    assert out.empty
