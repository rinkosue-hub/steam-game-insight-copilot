"""Tests for analyzer."""

import pandas as pd

from src.analyzer import basic_stats, extract_keywords


def test_basic_stats() -> None:
    """Basic stats should calculate counts and averages."""
    df = pd.DataFrame(
        {
            "sentiment": ["positive", "negative", "positive"],
            "playtime_hours": [1, 2, 3],
            "review_length": [10, 20, 30],
        }
    )
    stats = basic_stats(df)
    assert stats["total_reviews"] == 3
    assert stats["positive_count"] == 2
    assert round(stats["positive_rate"], 2) == 0.67


def test_extract_keywords_returns_list() -> None:
    """Keyword extraction should return list of tuples."""
    df = pd.DataFrame({"review_clean": ["玩法 很爽 构筑 很爽", "美术 音乐 很棒"]})
    keywords = extract_keywords(df, top_n=5)
    assert isinstance(keywords, list)
    assert keywords
    assert isinstance(keywords[0], tuple)
