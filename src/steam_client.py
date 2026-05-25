"""Steam review API client."""

from __future__ import annotations

import re
import time
from typing import Any, Optional

import pandas as pd
import requests


REVIEW_COLUMNS = [
    "recommendationid",
    "review",
    "voted_up",
    "timestamp_created",
    "timestamp_updated",
    "votes_up",
    "votes_funny",
    "weighted_vote_score",
    "playtime_forever",
    "playtime_at_review",
    "num_games_owned",
]


def parse_appid(input_text: str) -> Optional[str]:
    """Parse a Steam AppID from a numeric string or Steam store URL."""
    text = (input_text or "").strip()
    if re.fullmatch(r"\d+", text):
        return text
    match = re.search(r"store\.steampowered\.com/app/(\d+)", text)
    return match.group(1) if match else None


def _empty_reviews(error: Optional[str] = None) -> pd.DataFrame:
    """Create an empty review DataFrame with optional friendly error metadata."""
    df = pd.DataFrame(columns=REVIEW_COLUMNS)
    if error:
        df.attrs["error"] = error
    return df


def _normalize_review(item: dict[str, Any]) -> dict[str, Any]:
    """Normalize one Steam review and drop unnecessary user identity fields."""
    author = item.get("author") or {}
    return {
        "recommendationid": item.get("recommendationid"),
        "review": item.get("review", ""),
        "voted_up": bool(item.get("voted_up")),
        "timestamp_created": item.get("timestamp_created"),
        "timestamp_updated": item.get("timestamp_updated"),
        "votes_up": item.get("votes_up", 0),
        "votes_funny": item.get("votes_funny", 0),
        "weighted_vote_score": item.get("weighted_vote_score", 0),
        "playtime_forever": author.get("playtime_forever", 0),
        "playtime_at_review": author.get("playtime_at_review", 0),
        "num_games_owned": author.get("num_games_owned", 0),
    }


def fetch_reviews(
    appid: str,
    max_reviews: int = 500,
    language: str = "schinese",
    review_type: str = "all",
    purchase_type: str = "all",
    filter_type: str = "recent",
) -> pd.DataFrame:
    """Fetch Steam reviews with pagination and return a normalized DataFrame."""
    if not appid or not str(appid).isdigit():
        return _empty_reviews("AppID 无效，请输入 Steam AppID 或商店链接。")

    collected: list[dict[str, Any]] = []
    cursor = "*"
    session = requests.Session()
    max_reviews = max(1, int(max_reviews))

    while len(collected) < max_reviews:
        page_size = min(100, max_reviews - len(collected))
        url = f"https://store.steampowered.com/appreviews/{appid}"
        params = {
            "json": 1,
            "filter": filter_type,
            "language": language,
            "review_type": review_type,
            "purchase_type": purchase_type,
            "num_per_page": page_size,
            "cursor": cursor,
        }
        try:
            response = session.get(url, params=params, timeout=12)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException:
            return _empty_reviews("Steam 评论请求失败，请稍后重试或切换 Demo 模式。")
        except ValueError:
            return _empty_reviews("Steam 返回内容无法解析，请稍后再试。")

        reviews = payload.get("reviews") or []
        if not reviews:
            break

        collected.extend(_normalize_review(item) for item in reviews)
        next_cursor = payload.get("cursor")
        if not next_cursor or next_cursor == cursor:
            break
        cursor = next_cursor
        time.sleep(0.3)

    df = pd.DataFrame(collected[:max_reviews], columns=REVIEW_COLUMNS)
    if df.empty:
        df.attrs["error"] = "没有获取到评论，可能是语言/筛选条件下暂无数据。"
    return df
