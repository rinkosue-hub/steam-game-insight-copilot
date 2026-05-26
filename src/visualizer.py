"""Plotly chart builders."""

from __future__ import annotations

import html
import math
import random
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image, ImageDraw, ImageFont


def create_sentiment_chart(stats: dict):
    """Create a positive/negative review donut chart."""
    data = pd.DataFrame(
        {"sentiment": ["正向", "负向"], "count": [stats.get("positive_count", 0), stats.get("negative_count", 0)]}
    )
    return px.pie(data, names="sentiment", values="count", hole=0.45, title="正向 / 负向比例")


def create_keyword_chart(keywords: list[tuple[str, int]], title: str):
    """Create a keyword bar chart."""
    if not keywords:
        return None
    df = pd.DataFrame(keywords, columns=["keyword", "count"]).sort_values("count")
    return px.bar(df, x="count", y="keyword", orientation="h", title=title, labels={"count": "出现次数", "keyword": "关键词"})


def create_keyword_wordcloud(keywords: list[tuple[str, int]], title: str = "全部评论关键词"):
    """Create a lightweight word-cloud style chart with Plotly text markers."""
    if not keywords:
        return None

    top_keywords = keywords[:100]
    max_count = max(count for _, count in top_keywords) or 1
    min_count = min(count for _, count in top_keywords)
    span = max(max_count - min_count, 1)
    colors = ["#ff4b4b", "#0b65c2", "#00a86b", "#8a5cf6", "#f59f00", "#2f3542", "#00a3a3"]

    xs = []
    ys = []
    sizes = []
    texts = []
    hovers = []
    marker_colors = []
    for idx, (word, count) in enumerate(top_keywords):
        if idx == 0:
            radius = 0
            angle = 0
        else:
            radius = 0.18 * math.sqrt(idx)
            angle = idx * 2.399963229728653
        xs.append(radius * math.cos(angle))
        ys.append(radius * math.sin(angle))
        sizes.append(16 + 36 * ((count - min_count) / span))
        texts.append(word)
        hovers.append(f"关键词：{word}<br>出现次数：{count}")
        marker_colors.append(colors[idx % len(colors)])

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="text",
            text=texts,
            hovertext=hovers,
            hoverinfo="text",
            textfont={"size": sizes, "color": marker_colors},
        )
    )
    fig.update_layout(
        title=title,
        height=520,
        margin={"l": 10, "r": 10, "t": 70, "b": 10},
        xaxis={"visible": False, "range": [-1.75, 1.75]},
        yaxis={"visible": False, "range": [-1.25, 1.25]},
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return fig


def create_keyword_wordcloud_html(keywords: list[tuple[str, int]], title: str = "全部评论关键词词云") -> str:
    """Create an organic HTML word cloud with varied offsets while avoiding overlap."""
    if not keywords:
        return ""

    top_keywords = keywords[:120]
    max_count = max(count for _, count in top_keywords) or 1
    min_count = min(count for _, count in top_keywords)
    span = max(max_count - min_count, 1)
    colors = ["#ff4b4b", "#0b65c2", "#00a86b", "#8a5cf6", "#f59f00", "#2f3542", "#00a3a3", "#c92a2a"]
    chips = []
    for idx, (word, count) in enumerate(top_keywords):
        weight = (count - min_count) / span
        size = 16 + 52 * weight
        opacity = 0.68 + 0.32 * weight
        padding_y = 4 + 4 * weight
        padding_x = 8 + 10 * weight
        translate_y = [-10, 7, -4, 12, -7, 3, 0][idx % 7]
        rotate = [-7, 4, -3, 6, -5, 2, 0, 5][idx % 8]
        margin_left = [0, 18, 4, 30, 11, 24, 7, 15][idx % 8]
        margin_right = [15, 3, 24, 6, 19, 8, 28, 4][idx % 8]
        chips.append(
            "<span "
            f"title='关键词：{html.escape(str(word))}｜出现次数：{count}' "
            "style='"
            "display:inline-block;"
            f"font-size:{size:.1f}px;"
            f"line-height:{size * 1.18:.1f}px;"
            f"padding:{padding_y:.1f}px {padding_x:.1f}px;"
            f"margin:{max(2, 12 - weight * 6):.1f}px {margin_right}px {max(2, 10 - weight * 4):.1f}px {margin_left}px;"
            "font-weight:700;"
            f"color:{colors[idx % len(colors)]};"
            f"opacity:{opacity:.2f};"
            "white-space:nowrap;"
            "border-radius:999px;"
            "background:rgba(245,247,251,0.74);"
            "vertical-align:middle;"
            f"transform:translateY({translate_y}px) rotate({rotate}deg);"
            "'>"
            f"{html.escape(str(word))}"
            "</span>"
        )
    return (
        "<div style='margin: 10px 0 2px 0;'>"
        f"<h3 style='margin:0 0 16px 0;font-size:1.55rem;'>{html.escape(title)}</h3>"
        "<div style='"
        "display:flex;flex-wrap:wrap;align-items:center;align-content:center;"
        "gap:8px 10px;min-height:380px;padding:34px 34px;"
        "border:1px solid rgba(49,51,63,0.12);border-radius:14px;"
        "background:linear-gradient(180deg,#ffffff 0%,#f8fafc 100%);"
        "overflow:hidden;"
        "'>"
        + "".join(chips)
        + "</div></div>"
    )


def _font_candidates() -> list[str]:
    """Return candidate font paths that support Chinese and Latin text."""
    return [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a local font with graceful fallback."""
    candidates = _font_candidates()
    if bold:
        candidates = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/PingFang.ttc",
        ] + candidates
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def _rects_overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int], gap: int = 4) -> bool:
    """Return whether two rectangles overlap with a small gap."""
    return not (a[2] + gap < b[0] or b[2] + gap < a[0] or a[3] + gap < b[1] or b[3] + gap < a[1])


def create_keyword_wordcloud_image(
    keywords: list[tuple[str, int]],
    width: int = 1500,
    height: int = 720,
) -> Image.Image | None:
    """Create a dense bitmap word cloud similar to editorial word-cloud posters."""
    if not keywords:
        return None

    rng = random.Random(20260526)
    top_keywords = [(str(word), int(count)) for word, count in keywords[:130] if str(word).strip()]
    if not top_keywords:
        return None

    max_count = max(count for _, count in top_keywords) or 1
    min_count = min(count for _, count in top_keywords)
    span = max(max_count - min_count, 1)
    palette = [
        (60, 73, 92),
        (71, 119, 169),
        (98, 111, 122),
        (139, 125, 130),
        (166, 175, 179),
        (50, 95, 150),
        (112, 104, 110),
    ]

    image = Image.new("RGB", (width, height), "white")
    occupied: list[tuple[int, int, int, int]] = []
    center_x, center_y = width // 2, height // 2

    for idx, (word, count) in enumerate(top_keywords):
        weight = (count - min_count) / span
        base_size = int(18 + 92 * (weight ** 0.72))
        if idx < 5:
            base_size += 22 - idx * 3
        font = _load_font(base_size, bold=idx < 20)
        color = palette[idx % len(palette)]
        if idx > 12:
            fade = min(0.55, idx / max(len(top_keywords), 1))
            color = tuple(int(channel + (210 - channel) * fade) for channel in color)

        text_bbox = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), word, font=font)
        text_w = max(1, text_bbox[2] - text_bbox[0])
        text_h = max(1, text_bbox[3] - text_bbox[1])
        pad = max(8, base_size // 8)
        tile = Image.new("RGBA", (text_w + pad * 2, text_h + pad * 2), (255, 255, 255, 0))
        tile_draw = ImageDraw.Draw(tile)
        tile_draw.text((pad, pad - text_bbox[1]), word, font=font, fill=color + (255,))

        angle = 0
        if idx > 8:
            angle = rng.choice([-8, -5, -3, 0, 0, 0, 4, 6, 9])
        tile = tile.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
        tw, th = tile.size
        if tw >= width or th >= height:
            continue

        placed = False
        for attempt in range(950):
            if attempt < 650:
                radius = 5.2 * math.sqrt(attempt)
                theta = attempt * 2.399963229728653 + idx * 0.39
                x = int(center_x + radius * math.cos(theta) - tw / 2)
                y = int(center_y + radius * math.sin(theta) - th / 2)
            else:
                x = rng.randint(0, width - tw)
                y = rng.randint(0, height - th)
            rect = (x, y, x + tw, y + th)
            if x < 0 or y < 0 or rect[2] > width or rect[3] > height:
                continue
            if any(_rects_overlap(rect, other, gap=2) for other in occupied):
                continue
            image.paste(tile, (x, y), tile)
            occupied.append(rect)
            placed = True
            break

        if not placed and idx < 25:
            smaller = max(16, int(base_size * 0.72))
            fallback_font = _load_font(smaller, bold=idx < 15)
            bbox = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), word, font=fallback_font)
            fw, fh = bbox[2] - bbox[0] + pad * 2, bbox[3] - bbox[1] + pad * 2
            if fw < width and fh < height:
                for _ in range(500):
                    x = rng.randint(0, width - fw)
                    y = rng.randint(0, height - fh)
                    rect = (x, y, x + fw, y + fh)
                    if not any(_rects_overlap(rect, other, gap=2) for other in occupied):
                        ImageDraw.Draw(image).text((x + pad, y + pad - bbox[1]), word, font=fallback_font, fill=color)
                        occupied.append(rect)
                        break

    return image


def create_tag_distribution_chart(tag_summary_df: pd.DataFrame):
    """Create a player feedback topic distribution bar chart."""
    if tag_summary_df is None or tag_summary_df.empty:
        return None
    return px.bar(
        tag_summary_df.sort_values("count"),
        x="count",
        y="tag",
        orientation="h",
        title="玩家反馈主题分布",
        labels={"count": "评论数", "tag": "反馈主题"},
    )


def create_game_position_quadrant_chart(
    game_name: str,
    stats: dict,
    steam_median_playtime_hours: float = 10.0,
    steam_median_recommendation_rate: float = 0.75,
):
    """Create a single-game playtime-recommendation quadrant position chart."""
    if not stats:
        return None
    x_value = float(stats.get("median_playtime_hours", 0) or 0)
    y_value = float(stats.get("positive_rate", 0) or 0)
    x_ref = float(steam_median_playtime_hours)
    y_ref = float(steam_median_recommendation_rate)
    if x_value >= x_ref and y_value >= y_ref:
        quadrant = "高时长高推荐"
    elif x_value >= x_ref and y_value < y_ref:
        quadrant = "高时长低推荐"
    elif x_value < x_ref and y_value >= y_ref:
        quadrant = "低时长高推荐"
    else:
        quadrant = "低时长低推荐"

    fig = px.scatter(
        pd.DataFrame(
            [
                {
                    "game_name": game_name,
                    "median_playtime_hours": x_value,
                    "recommendation_rate": y_value,
                    "quadrant": quadrant,
                    "total_reviews": stats.get("total_reviews", 0),
                }
            ]
        ),
        x="median_playtime_hours",
        y="recommendation_rate",
        size="total_reviews",
        color="quadrant",
        text="game_name",
        hover_data={
            "game_name": True,
            "median_playtime_hours": ":.2f",
            "recommendation_rate": ":.2f",
            "total_reviews": True,
            "quadrant": True,
        },
        title="游戏位置图：游玩时长 × 推荐率",
        labels={
            "median_playtime_hours": "游玩时长中位数（小时）",
            "recommendation_rate": "推荐率",
            "total_reviews": "评论数",
        },
    )
    fig.update_traces(textposition="top center")
    fig.add_hline(y=y_ref, line_dash="dash", line_color="#666", annotation_text="Steam全站推荐率中位线")
    fig.add_vline(x=x_ref, line_dash="dash", line_color="#666", annotation_text="Steam全站游玩时长中位线")
    fig.update_xaxes(range=[0, max(x_value * 1.8, x_ref * 1.5, 2)])
    fig.update_yaxes(range=[0, 1])
    fig.update_layout(legend_title_text="象限")
    return fig


def create_quadrant_chart(quadrant_df: pd.DataFrame):
    """Create the legacy playtime-recommendation bubble quadrant chart by feedback topic."""
    if quadrant_df is None or quadrant_df.empty:
        return None
    median_x = float(quadrant_df["avg_playtime_hours"].median())
    fig = px.scatter(
        quadrant_df,
        x="avg_playtime_hours",
        y="recommendation_rate",
        size="count",
        color="quadrant",
        text="tag",
        hover_data={
            "tag": True,
            "count": True,
            "avg_playtime_hours": ":.2f",
            "recommendation_rate": ":.2f",
            "hotness_percent": ":.2f",
            "quadrant": True,
            "example_review": True,
        },
        title="反馈主题位置图：游玩时长 × 推荐率",
        labels={
            "avg_playtime_hours": "平均游玩时长（小时）",
            "recommendation_rate": "推荐率：该类反馈中正向占比",
            "hotness_percent": "出现占比（%）",
        },
    )
    fig.update_traces(textposition="top center")
    fig.add_hline(y=0.5, line_dash="dash", line_color="#666", annotation_text="推荐率中位线")
    fig.add_vline(x=median_x, line_dash="dash", line_color="#666", annotation_text="游玩时长中位线")
    fig.update_yaxes(range=[0, 1])
    fig.update_layout(legend_title_text="象限")
    return fig
