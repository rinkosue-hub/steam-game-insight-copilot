"""Competitor analysis workflow."""

from __future__ import annotations

import pandas as pd

from src.analyzer import basic_stats, extract_keywords
from src.classifier import build_quadrant_data, classify_reviews, load_tag_rules, tag_summary
from src.cleaner import clean_reviews
from src.steam_client import fetch_reviews


def analyze_single_game_for_competitor(
    appid: str,
    game_name: str,
    max_reviews: int = 300,
    language: str = "schinese",
) -> dict:
    """Analyze one game and return compact competitor metrics."""
    raw = fetch_reviews(appid, max_reviews=max_reviews, language=language)
    cleaned = clean_reviews(raw)
    rules = load_tag_rules()
    classified = classify_reviews(cleaned, rules)
    stats = basic_stats(classified)
    positive_df = classified[classified["sentiment"] == "positive"] if not classified.empty else classified
    negative_df = classified[classified["sentiment"] == "negative"] if not classified.empty else classified
    tags = tag_summary(classified)
    quadrant = build_quadrant_data(classified)
    core = quadrant[quadrant["quadrant"].isin(["高粘性卖点", "轻量正向体验"])]["tag"].tolist() if not quadrant.empty else []
    issues = quadrant[quadrant["quadrant"].isin(["深度体验痛点", "早期流失风险"])]["tag"].tolist() if not quadrant.empty else []
    return {
        "game_name": game_name,
        "appid": appid,
        "total_reviews": stats["total_reviews"],
        "positive_rate": stats["positive_rate"],
        "avg_playtime_hours": stats["avg_playtime_hours"],
        "top_positive_keywords": "、".join([word for word, _ in extract_keywords(positive_df, language=language, top_n=8)]),
        "top_negative_keywords": "、".join([word for word, _ in extract_keywords(negative_df, language=language, top_n=8)]),
        "top_tags": "、".join(tags["tag"].head(5).tolist()) if not tags.empty else "",
        "core_selling_points": "、".join(core),
        "priority_issues": "、".join(issues),
    }


def analyze_multiple_games(games: list[dict], max_reviews: int = 300, language: str = "schinese") -> pd.DataFrame:
    """Analyze multiple competitor games into a comparison table."""
    rows = []
    for game in games:
        appid = str(game.get("appid", "")).strip()
        name = game.get("game_name") or appid
        if appid:
            rows.append(analyze_single_game_for_competitor(appid, name, max_reviews, language))
    return pd.DataFrame(rows)


def generate_competitor_report(summary_df: pd.DataFrame) -> str:
    """Generate a markdown competitor analysis report from summary rows."""
    if summary_df is None or summary_df.empty:
        return "# Steam 竞品反馈分析报告\n\n暂无可分析数据。"

    best = summary_df.sort_values("positive_rate", ascending=False).iloc[0]
    table = summary_df.copy()
    table["positive_rate"] = table["positive_rate"].map(lambda value: f"{value * 100:.1f}%")
    headers = list(table.columns)
    markdown_table = "| " + " | ".join(headers) + " |\n"
    markdown_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    for row in table.itertuples(index=False):
        markdown_table += "| " + " | ".join(str(value) for value in row) + " |\n"
    strengths = "\n".join([f"- {row.game_name}: {row.core_selling_points or row.top_positive_keywords or '暂无明显认可点'}" for row in summary_df.itertuples()])
    issues = "\n".join([f"- {row.game_name}: {row.priority_issues or row.top_negative_keywords or '暂无明显吐槽点'}" for row in summary_df.itertuples()])
    return f"""# Steam 竞品反馈分析报告

## 1. 竞品整体表现
本次共分析 {len(summary_df)} 款游戏。当前样本中口碑最高的是 {best.game_name}，推荐率约 {best.positive_rate * 100:.1f}%。对比表如下：

{markdown_table}

## 2. 各游戏玩家认可点
{strengths}

## 3. 各游戏玩家吐槽点
{issues}

## 4. 四象限对比结论
若某竞品的核心卖点高度集中，说明它已经形成明确传播钩子；若优先修复问题集中在性能、BUG 或平衡性，则说明其体验短板可能成为目标产品切入机会。

## 5. 产品机会点
- 选择竞品高正向关键词作为基础体验门槛，避免在玩家已默认期待的维度失分。
- 对竞品高频负向标签做反向设计，形成“同类痛点更少”的差异化表达。
- 将高认可标签转化为商店页卖点，将高吐槽标签转化为版本验证清单。

## 6. 对目标产品的启发
目标产品应同时关注“能被玩家一句话推荐的卖点”和“会阻断推荐的体验问题”。竞品分析不是复制玩法，而是识别玩家评价标准，再把这些标准转化为研发、运营、宣发之间共用的决策语言。
"""
