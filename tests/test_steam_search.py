"""Tests for Steam search."""

import pandas as pd

from src import steam_search


def test_search_games_by_name_returns_dataframe(monkeypatch) -> None:
    """Search should parse appid and name from mocked Steam HTML."""

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "results_html": """
                <a class="search_result_row" data-ds-appid="1942280" href="https://store.steampowered.com/app/1942280/Brotato/">
                    <span class="title">Brotato</span>
                    <div class="search_price">¥22</div>
                    <div class="search_released">Jun 23, 2023</div>
                    <span class="search_review_summary" data-tooltip-html="特别好评"></span>
                </a>
                """
            }

    monkeypatch.setattr(steam_search.requests, "get", lambda *args, **kwargs: FakeResponse())
    df = steam_search.search_games_by_name("Brotato")
    assert isinstance(df, pd.DataFrame)
    assert {"appid", "name"}.issubset(df.columns)
    assert df.iloc[0]["appid"] == "1942280"
    assert df.iloc[0]["name"] == "Brotato"
