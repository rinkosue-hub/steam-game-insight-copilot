"""Steam store search helpers."""

from __future__ import annotations

import re
from typing import Any, Optional
from urllib.parse import quote_plus

import pandas as pd
import requests
from bs4 import BeautifulSoup


SEARCH_COLUMNS = ["appid", "name", "price", "release_date", "review_summary", "store_url"]

FALLBACK_GAMES = [
    {
        "appid": "1942280",
        "name": "Brotato",
        "aliases": ["brotato", "土豆兄弟", "土豆", "马铃薯兄弟", "土豆幸存者", "兄弟土豆"],
        "price": "",
        "release_date": "2023",
        "review_summary": "",
        "store_url": "https://store.steampowered.com/app/1942280/Brotato/",
    },
    {
        "appid": "1794680",
        "name": "Vampire Survivors",
        "aliases": ["vampire survivors", "吸血鬼幸存者"],
        "price": "",
        "release_date": "2022",
        "review_summary": "",
        "store_url": "https://store.steampowered.com/app/1794680/Vampire_Survivors/",
    },
    {
        "appid": "1468810",
        "name": "鬼谷八荒",
        "aliases": ["鬼谷八荒", "tale of immortal"],
        "price": "",
        "release_date": "2023",
        "review_summary": "",
        "store_url": "https://store.steampowered.com/app/1468810/_/",
    },
    {
        "appid": "367520",
        "name": "Hollow Knight",
        "aliases": ["hollow knight", "空洞骑士"],
        "price": "",
        "release_date": "2017",
        "review_summary": "",
        "store_url": "https://store.steampowered.com/app/367520/Hollow_Knight/",
    },
    {
        "appid": "413150",
        "name": "Stardew Valley",
        "aliases": ["stardew valley", "星露谷物语", "星露谷"],
        "price": "",
        "release_date": "2016",
        "review_summary": "",
        "store_url": "https://store.steampowered.com/app/413150/Stardew_Valley/",
    },
    {
        "appid": "105600",
        "name": "Terraria",
        "aliases": ["terraria", "泰拉瑞亚"],
        "price": "",
        "release_date": "2011",
        "review_summary": "",
        "store_url": "https://store.steampowered.com/app/105600/Terraria/",
    },
    {
        "appid": "322330",
        "name": "Don't Starve Together",
        "aliases": ["don't starve together", "dont starve together", "饥荒联机版", "饥荒"],
        "price": "",
        "release_date": "2016",
        "review_summary": "",
        "store_url": "https://store.steampowered.com/app/322330/Dont_Starve_Together/",
    },
    {
        "appid": "578080",
        "name": "PUBG: BATTLEGROUNDS",
        "aliases": ["pubg", "绝地求生", "吃鸡"],
        "price": "",
        "release_date": "2017",
        "review_summary": "",
        "store_url": "https://store.steampowered.com/app/578080/PUBG_BATTLEGROUNDS/",
    },
    {
        "appid": "730",
        "name": "Counter-Strike 2",
        "aliases": ["counter-strike 2", "counter strike 2", "cs2", "反恐精英2", "反恐精英"],
        "price": "",
        "release_date": "2023",
        "review_summary": "",
        "store_url": "https://store.steampowered.com/app/730/CounterStrike_2/",
    },
    {
        "appid": "2358720",
        "name": "Black Myth: Wukong",
        "aliases": ["black myth wukong", "black myth: wukong", "黑神话悟空", "黑神话：悟空", "悟空"],
        "price": "",
        "release_date": "2024",
        "review_summary": "",
        "store_url": "https://store.steampowered.com/app/2358720/Black_Myth_Wukong/",
    },
    {
        "appid": "1245620",
        "name": "ELDEN RING",
        "aliases": ["elden ring", "艾尔登法环", "老头环"],
        "price": "",
        "release_date": "2022",
        "review_summary": "",
        "store_url": "https://store.steampowered.com/app/1245620/ELDEN_RING/",
    },
    {
        "appid": "1091500",
        "name": "Cyberpunk 2077",
        "aliases": ["cyberpunk 2077", "赛博朋克2077", "赛博朋克 2077"],
        "price": "",
        "release_date": "2020",
        "review_summary": "",
        "store_url": "https://store.steampowered.com/app/1091500/Cyberpunk_2077/",
    },
]


def _normalize_query(value: str) -> str:
    """Normalize a game query for loose alias matching."""
    return re.sub(r"[\s:：_\-·，,。.!！?？]+", "", (value or "").strip().lower())


def _fallback_search(query: str, max_results: int) -> pd.DataFrame:
    """Return local fallback search rows for common demo games."""
    normalized = _normalize_query(query)
    rows = []
    for game in FALLBACK_GAMES:
        haystack = [_normalize_query(game["name"])] + [_normalize_query(alias) for alias in game["aliases"]]
        if any(normalized in item or item in normalized for item in haystack):
            rows.append({key: game[key] for key in SEARCH_COLUMNS})
    return pd.DataFrame(rows[:max_results], columns=SEARCH_COLUMNS)


def _parse_result_row(row: Any) -> Optional[dict[str, str]]:
    """Parse one Steam search result row from HTML."""
    appid = (
        row.get("data-ds-appid")
        or row.get("data-ds-bundleid")
        or row.get("data-ds-itemkey", "").replace("App_", "")
        or ""
    )
    href = row.get("href", "")
    if not appid:
        match = re.search(r"/app/(\d+)", href)
        appid = match.group(1) if match else ""
    title = row.select_one(".title")
    if not appid or not title:
        return None
    price = row.select_one(".search_price, .discount_final_price")
    release = row.select_one(".search_released")
    review = row.select_one(".search_review_summary")
    return {
        "appid": str(appid).split(",")[0],
        "name": title.get_text(" ", strip=True),
        "price": price.get_text(" ", strip=True) if price else "",
        "release_date": release.get_text(" ", strip=True) if release else "",
        "review_summary": review.get("data-tooltip-html", "") if review else "",
        "store_url": href,
    }


def _search_store_api(query: str, max_results: int) -> list[dict[str, str]]:
    """Search Steam's lightweight storesearch API."""
    try:
        response = requests.get(
            "https://store.steampowered.com/api/storesearch/",
            params={"term": query, "l": "schinese", "cc": "cn", "category1": 998, "count": max_results},
            timeout=12,
            headers={"User-Agent": "SteamGameInsightCopilot/1.0"},
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return []

    rows = []
    for item in payload.get("items", []) or []:
        appid = str(item.get("id") or item.get("appid") or "")
        name = item.get("name") or ""
        if appid.isdigit() and name:
            rows.append(
                {
                    "appid": appid,
                    "name": name,
                    "price": item.get("price", {}).get("final", "") if isinstance(item.get("price"), dict) else "",
                    "release_date": "",
                    "review_summary": "",
                    "store_url": f"https://store.steampowered.com/app/{appid}/{quote_plus(name)}/",
                }
            )
    return rows


def search_games_by_name(query: str, max_results: int = 10) -> pd.DataFrame:
    """Search Steam store games by name and return structured candidates."""
    if not (query or "").strip():
        return pd.DataFrame(columns=SEARCH_COLUMNS)
    fallback = _fallback_search(query, max_results)
    if not fallback.empty:
        return fallback
    api_rows = _search_store_api(query, max_results)
    if api_rows:
        return pd.DataFrame(api_rows[:max_results], columns=SEARCH_COLUMNS)
    try:
        response = requests.get(
            "https://store.steampowered.com/search/results/",
            params={"term": query, "json": 1, "count": max_results, "category1": 998, "l": "schinese", "cc": "cn"},
            timeout=12,
            headers={"User-Agent": "SteamGameInsightCopilot/1.0"},
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return fallback

    rows: list[dict[str, str]] = []
    html = payload.get("results_html") or ""
    if html:
        soup = BeautifulSoup(html, "html.parser")
        for row in soup.select("a.search_result_row"):
            parsed = _parse_result_row(row)
            if parsed:
                rows.append(parsed)

    if not rows and isinstance(payload.get("items"), list):
        for item in payload["items"]:
            rows.append(
                {
                    "appid": str(item.get("id") or item.get("appid") or ""),
                    "name": item.get("name") or "",
                    "price": item.get("price") or "",
                    "release_date": item.get("release_date") or "",
                    "review_summary": item.get("review_summary") or "",
                    "store_url": item.get("url") or "",
                }
            )

    result = pd.DataFrame(rows[:max_results], columns=SEARCH_COLUMNS)
    if result.empty or not result["appid"].astype(str).str.fullmatch(r"\d+").any():
        return fallback
    result["appid"] = result["appid"].astype(str)
    return result[result["appid"].str.fullmatch(r"\d+")].reset_index(drop=True)
