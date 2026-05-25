"""Tests for review cleaning."""

import pandas as pd

from src.cleaner import clean_reviews


def test_clean_reviews_html_sentiment_playtime() -> None:
    """Cleaner should strip HTML and add derived fields."""
    df = pd.DataFrame(
        {
            "review": ["<b>玩法 很爽</b>\n值得买"],
            "voted_up": [True],
            "timestamp_created": [1710000000],
            "timestamp_updated": [1710000000],
            "playtime_forever": [120],
        }
    )
    cleaned = clean_reviews(df)
    assert cleaned.loc[0, "review_clean"] == "玩法 很爽 值得买"
    assert cleaned.loc[0, "sentiment"] == "positive"
    assert cleaned.loc[0, "playtime_hours"] == 2
