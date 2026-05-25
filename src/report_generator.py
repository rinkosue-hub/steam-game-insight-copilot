"""Markdown report generation with optional OpenAI polishing."""

from __future__ import annotations

import os

import pandas as pd
from dotenv import load_dotenv


def _fmt_rate(value: float) -> str:
    """Format a 0-1 rate as percentage."""
    return f"{value * 100:.1f}%"


def _kw_text(keywords: list, limit: int = 10) -> str:
    """Format keywords for markdown."""
    return "、".join([f"{word}({count})" for word, count in keywords[:limit]]) or "暂无明显关键词"


def _tags_by_quadrant(quadrant_df: pd.DataFrame, quadrant: str) -> str:
    """Return comma separated tags in a quadrant."""
    if quadrant_df is None or quadrant_df.empty:
        return "暂无"
    rows = quadrant_df[quadrant_df["quadrant"] == quadrant]
    if rows.empty:
        return "暂无"
    return "、".join([f"{row.tag}({row.count}条)" for row in rows.itertuples()])


def _template_report(
    game_name: str,
    appid: str,
    stats: dict,
    keywords_all: list,
    keywords_positive: list,
    keywords_negative: list,
    tag_summary_df: pd.DataFrame,
    quadrant_df: pd.DataFrame,
    top_reviews_df: pd.DataFrame,
) -> str:
    """Generate a deterministic markdown report."""
    positive_rate = stats.get("positive_rate", 0)
    if positive_rate >= 0.8:
        tone = "玩家口碑较强，当前反馈更适合用于卖点提炼和增量优化。"
    elif positive_rate >= 0.6:
        tone = "玩家认可与吐槽并存，建议围绕高频负反馈做版本优先级排序。"
    else:
        tone = "当前负向反馈压力较高，需要优先定位影响体验和转化的关键问题。"

    tag_lines = "暂无标签数据"
    if tag_summary_df is not None and not tag_summary_df.empty:
        tag_lines = "\n".join(
            [f"- {row.tag}: {row.count} 条，占比 {row.ratio * 100:.1f}%。代表反馈：{row.example_review[:80]}" for row in tag_summary_df.itertuples()]
        )

    p0 = _tags_by_quadrant(quadrant_df, "深度体验痛点")
    early_risk = _tags_by_quadrant(quadrant_df, "早期流失风险")
    core = _tags_by_quadrant(quadrant_df, "高粘性卖点")
    light_positive = _tags_by_quadrant(quadrant_df, "轻量正向体验")
    split = _tags_by_quadrant(quadrant_df, "分歧反馈")
    top_review_lines = "暂无"
    if top_reviews_df is not None and not top_reviews_df.empty:
        top_review_lines = "\n".join([f"- {row.review_clean[:120]}" for row in top_reviews_df.head(5).itertuples()])

    return f"""# Steam 玩家反馈分析报告

游戏：{game_name}（AppID: {appid}）

## 1. 数据概览
- 评论数：{stats.get("total_reviews", 0)}
- 正向数：{stats.get("positive_count", 0)}
- 负向数：{stats.get("negative_count", 0)}
- 推荐率：{_fmt_rate(stats.get("positive_rate", 0))}
- 平均游玩时长：{stats.get("avg_playtime_hours", 0):.1f} 小时
- 中位数游玩时长：{stats.get("median_playtime_hours", 0):.1f} 小时
- 平均评论长度：{stats.get("avg_review_length", 0):.1f} 字符

结论：{tone}

## 2. 全部评论关键词
全部评论高频词集中在：{_kw_text(keywords_all, 12)}。

结论：这些词反映玩家对游戏的第一层感知，可用于快速判断评论区讨论焦点。

## 3. 玩家正向反馈
正向关键词：{_kw_text(keywords_positive)}

结论：正向反馈主要围绕 {_kw_text(keywords_positive, 8)}，可沉淀为商店页、短视频素材和社区运营话术。

业务解释：这些词可以理解为玩家愿意推荐游戏的直接理由。若关键词集中在玩法、构筑、音乐、美术等维度，说明产品已经形成可传播的体验钩子，应优先用于商店页截图文案、主播沟通 brief 和社区内容二创引导。

## 4. 玩家负向反馈
负向关键词：{_kw_text(keywords_negative)}

结论：负向反馈主要围绕 {_kw_text(keywords_negative, 8)}，建议进入版本问题池并按影响面排序。

业务解释：负向关键词代表玩家在购买决策、留存体验或版本评价中的阻力。若集中在性能、BUG、平衡、内容重复等维度，应优先转化为可验证的迭代任务，并在更新公告中明确回应。

## 5. 高频问题归因
{tag_lines}

结论：高粘性卖点为 {core}；深度体验痛点为 {p0}；早期流失风险为 {early_risk}。

## 6. 游玩时长 × 推荐率四象限分析
- 高粘性卖点：{core}
- 深度体验痛点：{p0}
- 轻量正向体验：{light_positive}
- 早期流失风险：{early_risk}
- 分歧反馈：{split}

## 7. 可执行优化建议
- P0：优先处理“深度体验痛点”和“早期流失风险”中的标签，尤其是会直接造成负向推荐、退款或低时长流失的问题。
- P1：围绕“分歧反馈”做分层验证，区分硬核玩家偏好与新手玩家阻力，避免一刀切改动。
- P2：把“高粘性卖点”和“轻量正向体验”沉淀成宣发素材，包括商店页短句、更新日志亮点和社区话题。

## 8. 后续观察指标
- 推荐率变化，尤其是版本更新后 7 天内新增评论的情感变化。
- 性能、BUG、平衡性、新手引导等标签的负向评论占比。
- 平均游玩时长和中位数游玩时长是否随版本优化提升。
- 高有用评论中重复出现的问题是否被玩家持续顶起。

## 9. 其他结论
若某些结论无法直接归入关键词、反馈主题、位置图或高有用评论板块，可在这里沉淀为后续人工复盘问题。

## 附录：高有用评论摘录
{top_review_lines}
"""


def _polish_with_openai(report: str) -> str:
    """Optionally polish report with OpenAI when the SDK and key are available."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return report
    try:
        from openai import OpenAI  # type: ignore

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "你是游戏行业用户研究与运营分析顾问，请润色 Markdown 报告，保留结构和数据。"},
                {"role": "user", "content": report},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content or report
    except Exception:
        return report


def generate_single_game_report(
    game_name: str,
    appid: str,
    stats: dict,
    keywords_all: list,
    keywords_positive: list,
    keywords_negative: list,
    tag_summary_df: pd.DataFrame,
    quadrant_df: pd.DataFrame,
    top_reviews_df: pd.DataFrame,
) -> str:
    """Generate a Steam single-game feedback analysis report."""
    report = _template_report(
        game_name,
        appid,
        stats,
        keywords_all,
        keywords_positive,
        keywords_negative,
        tag_summary_df,
        quadrant_df,
        top_reviews_df,
    )
    return _polish_with_openai(report)
