"""Streamlit UI for Steam Game Insight Copilot."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.analyzer import basic_stats, extract_sentiment_phrases, extract_keywords, get_top_helpful_reviews
from src.classifier import build_quadrant_data, classify_reviews, load_tag_rules, tag_summary
from src.cleaner import clean_reviews
from src.competitor import analyze_multiple_games, generate_competitor_report
from src.exporter import create_zip_export, save_dataframe_csv, save_markdown_report
from src.report_generator import generate_single_game_report
from src.steam_client import fetch_reviews, parse_appid
from src.steam_search import search_games_by_name
from src.utils import first_error_message
from src.visualizer import (
    create_game_position_quadrant_chart,
    create_keyword_chart,
    create_keyword_wordcloud_image,
    create_quadrant_chart,
    create_sentiment_chart,
    create_tag_distribution_chart,
)


load_dotenv()
st.set_page_config(page_title="Steam Game Insight Copilot", page_icon="🎮", layout="wide")
STEAM_MEDIAN_PLAYTIME_HOURS = 10.0
STEAM_MEDIAN_RECOMMENDATION_RATE = 0.75


def run_pipeline(raw_df: pd.DataFrame, game_name: str, appid: str, language: str) -> dict:
    """Run the complete single-game analysis pipeline."""
    cleaned = clean_reviews(raw_df)
    rules = load_tag_rules()
    classified = classify_reviews(cleaned, rules)
    stats = basic_stats(classified)
    positive_df = classified[classified["sentiment"] == "positive"] if not classified.empty else classified
    negative_df = classified[classified["sentiment"] == "negative"] if not classified.empty else classified
    keywords_all = extract_keywords(classified, language=language, top_n=120)
    keywords_positive = extract_sentiment_phrases(positive_df, language=language, polarity="positive", top_n=50)
    keywords_negative = extract_sentiment_phrases(negative_df, language=language, polarity="negative", top_n=50)
    if not keywords_positive:
        keywords_positive = extract_keywords(positive_df, language=language, top_n=50)
    if not keywords_negative:
        keywords_negative = extract_keywords(negative_df, language=language, top_n=50)
    tags = tag_summary(classified)
    quadrant = build_quadrant_data(classified)
    top_reviews = get_top_helpful_reviews(classified)
    report = generate_single_game_report(
        game_name,
        appid,
        stats,
        keywords_all,
        keywords_positive,
        keywords_negative,
        tags,
        quadrant,
        top_reviews,
    )
    return {
        "df": classified,
        "game_name": game_name,
        "appid": appid,
        "stats": stats,
        "keywords_all": keywords_all,
        "keywords_positive": keywords_positive,
        "keywords_negative": keywords_negative,
        "tag_summary": tags,
        "quadrant": quadrant,
        "top_reviews": top_reviews,
        "report": report,
    }


def render_metrics(stats: dict) -> None:
    """Render key metric cards."""
    cols = st.columns(6)
    cols[0].metric("评论总数", stats.get("total_reviews", 0))
    cols[1].metric("正向数", stats.get("positive_count", 0))
    cols[2].metric("负向数", stats.get("negative_count", 0))
    cols[3].metric("正向率", f"{stats.get('positive_rate', 0) * 100:.1f}%")
    cols[4].metric("平均游玩时长", f"{stats.get('avg_playtime_hours', 0):.1f}h")
    cols[5].metric("中位数游玩时长", f"{stats.get('median_playtime_hours', 0):.1f}h")


def render_downloads(result: dict, prefix: str) -> None:
    """Render export buttons and persist files for history."""
    try:
        csv_path = save_dataframe_csv(result["df"], prefix)
        md_path = save_markdown_report(result["report"], prefix)
        zip_path = create_zip_export([csv_path, md_path], prefix)
    except Exception:
        st.warning("文件保存失败，但页面上的分析结果仍可查看。")
        return
    cols = st.columns(3)
    cols[0].download_button("下载 CSV", Path(csv_path).read_bytes(), file_name=Path(csv_path).name)
    cols[1].download_button("下载 Markdown", Path(md_path).read_text(encoding="utf-8"), file_name=Path(md_path).name)
    cols[2].download_button("下载 ZIP", Path(zip_path).read_bytes(), file_name=Path(zip_path).name)


def _format_game_option(item: dict) -> str:
    """Format a searched game candidate for the compact selector."""
    release = f" | {item.get('release_date')}" if item.get("release_date") else ""
    return f"{item.get('name')} | AppID {item.get('appid')}{release}"


def _resolve_selected_game(input_text: str, allow_warning: bool = True) -> dict | None:
    """Resolve user input into a selected game, searching by name when needed."""
    appid = parse_appid(input_text)
    if appid:
        selected = {"appid": appid, "game_name": input_text.strip() or appid}
        st.session_state["selected_game"] = selected
        return selected

    results = search_games_by_name(input_text, max_results=8)
    if results.empty:
        if allow_warning:
            st.error("没有搜索到匹配游戏。可以尝试输入英文名、中文常用名、AppID 或 Steam 商店链接。")
        return None

    results["appid"] = results["appid"].astype(str)
    results = results[results["appid"].str.fullmatch(r"\d+")].reset_index(drop=True)
    if results.empty:
        if allow_warning:
            st.error("搜索结果缺少可用 AppID，请直接输入 Steam AppID 或商店链接。")
        return None

    st.session_state["search_results"] = results
    first = results.iloc[0]
    selected = {"appid": str(first["appid"]), "game_name": str(first["name"])}
    st.session_state["selected_game"] = selected
    return selected


def _keywords_text(keywords: list[tuple[str, int]], limit: int = 8) -> str:
    """Format keywords for short page insights."""
    return "、".join([word for word, _ in keywords[:limit]]) or "暂无明显关键词"


def _render_insight(title: str, body: str) -> None:
    """Render a compact insight callout under a section."""
    st.info(f"**{title}**  \n{body}")


def _render_helpful_review_cards(df: pd.DataFrame) -> None:
    """Render helpful reviews as readable cards instead of a raw table."""
    if df is None or df.empty:
        st.info("暂无高有用评论。")
        return
    for idx, row in enumerate(df.head(10).itertuples(), start=1):
        sentiment = "正向" if getattr(row, "sentiment", "") == "positive" else "负向"
        tags = getattr(row, "tags", []) or []
        tag_text = "、".join(tags) if isinstance(tags, list) else str(tags)
        playtime = getattr(row, "playtime_hours", 0)
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([0.8, 0.8, 1, 4])
            c1.metric("序号", idx)
            c2.metric("倾向", sentiment)
            c3.metric("有用票", int(getattr(row, "votes_up", 0) or 0))
            c4.caption(f"游玩时长：{float(playtime or 0):.1f} 小时｜主题：{tag_text or '未命中'}")
            st.write(str(getattr(row, "review_clean", ""))[:420])


def single_game_page() -> None:
    """Render single-game analysis page."""
    st.title("Steam Game Insight Copilot")
    st.caption("从 Steam 玩家评论到反馈主题、游玩时长 × 推荐率位置和 Markdown 分析报告。")

    with st.container(border=True):
        cols = st.columns([2.7, 0.72, 0.82, 0.82, 0.92, 0.82, 0.92])
        input_text = cols[0].text_input("游戏 / AppID / 链接", placeholder="例如：黑神话悟空、Brotato、1942280")
        max_reviews = cols[1].selectbox("数量", [100, 500, 1000], index=1)
        language = cols[2].selectbox("语言", ["schinese", "english", "all"], format_func={"schinese": "中文", "english": "英文", "all": "全部"}.get)
        review_type = cols[3].selectbox("评论", ["all", "positive", "negative"], format_func={"all": "全部", "positive": "正向", "negative": "负向"}.get)
        purchase_type = cols[4].selectbox("来源", ["all", "steam", "non_steam_purchase"], format_func={"all": "全部", "steam": "Steam购买", "non_steam_purchase": "非Steam"}.get)
        filter_type = cols[5].selectbox("排序", ["recent", "updated", "all"], format_func={"recent": "最近", "updated": "更新", "all": "全部"}.get)
        start = cols[6].button("开始分析", type="primary", use_container_width=True)

        if input_text != st.session_state.get("last_single_game_input"):
            st.session_state["last_single_game_input"] = input_text
            st.session_state.pop("selected_game", None)
            st.session_state.pop("search_results", None)

        if "search_results" in st.session_state:
            results = st.session_state["search_results"].copy()
            records = results.to_dict("records")
            if len(records) > 1:
                options = [_format_game_option(item) for item in records]
                current_appid = str(st.session_state.get("selected_game", {}).get("appid", ""))
                default_index = next((idx for idx, item in enumerate(records) if str(item["appid"]) == current_appid), 0)
                choice = st.selectbox("候选游戏", options, index=default_index, label_visibility="collapsed")
                item = records[options.index(choice)]
                st.session_state["selected_game"] = {"appid": str(item["appid"]), "game_name": item["name"]}

        selected = st.session_state.get("selected_game")
        if selected and str(selected.get("appid", "")).isdigit():
            st.caption(f"已选择：{selected['game_name']}（AppID: {selected['appid']}）")

    if start:
        if not input_text.strip():
            st.error("请输入游戏名称、AppID 或 Steam 商店链接。")
            return
        selected = st.session_state.get("selected_game") or _resolve_selected_game(input_text)
        if not selected:
            return
        with st.spinner("正在获取 Steam 评论并生成分析..."):
            raw_df = fetch_reviews(
                selected["appid"],
                max_reviews=max_reviews,
                language=language,
                review_type=review_type,
                purchase_type=purchase_type,
                filter_type=filter_type,
            )
            error = first_error_message(raw_df)
            if raw_df.empty:
                st.error(error or "没有获取到评论，请调整语言或筛选条件。")
                return
            result = run_pipeline(raw_df, selected["game_name"], selected["appid"], language)
            st.session_state["analysis_result"] = result
            st.session_state["analysis_prefix"] = f"{selected['game_name']}_{selected['appid']}"

    result = st.session_state.get("analysis_result")
    if not result:
        return

    render_metrics(result["stats"])
    overview = (
        f"当前样本推荐率为 {result['stats'].get('positive_rate', 0) * 100:.1f}%，"
        f"游玩时长中位数为 {result['stats'].get('median_playtime_hours', 0):.1f} 小时。"
        "这两个指标会用于判断该游戏在“游玩时长 × 推荐率”坐标中的位置。"
    )
    _render_insight("数据概览解读", overview)

    col_a, col_b = st.columns(2)
    col_a.plotly_chart(create_sentiment_chart(result["stats"]), use_container_width=True)
    tag_fig = create_tag_distribution_chart(result["tag_summary"])
    if tag_fig:
        col_b.plotly_chart(tag_fig, use_container_width=True)
        top_tags = "、".join(result["tag_summary"]["tag"].head(5).tolist())
        _render_insight("反馈主题解读", f"玩家讨论最集中的主题是：{top_tags}。这些主题可以作为版本复盘和需求拆解的一级目录。")
    else:
        col_b.info("暂无可命中的反馈主题。")

    wordcloud_image = create_keyword_wordcloud_image(result["keywords_all"])
    if wordcloud_image:
        st.subheader("全部评论关键词词云")
        st.image(wordcloud_image, use_container_width=True)
        _render_insight("关键词解读", f"全部评论中最突出的词包括：{_keywords_text(result['keywords_all'])}。这些词反映玩家对游戏的第一层感知。")

    for title, keywords in [
        ("正向情绪短语", result["keywords_positive"]),
        ("负向情绪短语", result["keywords_negative"]),
    ]:
        fig = create_keyword_chart(keywords, title)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    game_position_fig = create_game_position_quadrant_chart(
        result["game_name"],
        result["stats"],
        STEAM_MEDIAN_PLAYTIME_HOURS,
        STEAM_MEDIAN_RECOMMENDATION_RATE,
    )
    if game_position_fig:
        st.plotly_chart(game_position_fig, use_container_width=True)
        _render_insight(
            "位置图解读",
            f"该图用本游戏样本的游玩时长中位数和推荐率定位位置；参考线使用 Steam 全站游戏基准：游玩时长中位数 {STEAM_MEDIAN_PLAYTIME_HOURS:.1f} 小时，推荐率中位线 {STEAM_MEDIAN_RECOMMENDATION_RATE * 100:.0f}%。右上代表相对全站基准玩得久且愿意推荐；右下代表深度体验后仍不推荐，需要重点复盘后期体验或核心系统。",
        )

    topic_position_fig = create_quadrant_chart(result["quadrant"])
    if topic_position_fig:
        with st.expander("查看反馈主题在游玩时长 × 推荐率中的位置"):
            st.plotly_chart(topic_position_fig, use_container_width=True)
    else:
        st.info("暂无主题位置数据：当前评论没有命中反馈主题。")

    st.subheader("高有用评论 Top 10")
    st.caption("有用票：Steam 用户认为这条评论“有帮助”的投票数，通常代表该评论对购买决策或问题共识更有参考价值。")
    _render_helpful_review_cards(result["top_reviews"])
    _render_insight("高有用评论解读", "这些评论被更多玩家标记为有用，通常更接近购买决策、退款原因或社区共识，适合作为报告引用和问题复盘样本。")

    st.subheader("导出分析结果")
    render_downloads(result, st.session_state.get("analysis_prefix", "steam_report"))


def competitor_page() -> None:
    """Render competitor analysis page."""
    st.title("竞品对比分析")
    lines = st.text_area("每行输入一款游戏名称 / AppID / 商店链接", height=160)
    max_reviews = st.selectbox("评论数量", [100, 300, 500], index=1)
    language = st.selectbox("评论语言", ["schinese", "english", "all"])
    if st.button("开始竞品分析", type="primary"):
        if not lines.strip():
            st.error("请至少输入一款游戏。")
            return
        games = []
        with st.spinner("正在解析游戏并拉取评论..."):
            for line in [item.strip() for item in lines.splitlines() if item.strip()]:
                appid = parse_appid(line)
                name = line
                if not appid:
                    results = search_games_by_name(line, max_results=1)
                    if results.empty:
                        st.warning(f"未找到：{line}")
                        continue
                    appid = str(results.iloc[0]["appid"])
                    name = str(results.iloc[0]["name"])
                games.append({"appid": appid, "game_name": name})
            if not games:
                st.error("没有可分析的游戏，请检查输入。")
                return
            summary = analyze_multiple_games(games, max_reviews=max_reviews, language=language)
            report = generate_competitor_report(summary)
            st.session_state["competitor_summary"] = summary
            st.session_state["competitor_report"] = report

    summary = st.session_state.get("competitor_summary")
    report = st.session_state.get("competitor_report")
    if summary is not None:
        st.dataframe(summary, use_container_width=True)
        st.markdown(report)
        csv_path = save_dataframe_csv(summary, "competitor_summary")
        md_path = save_markdown_report(report, "competitor_report")
        st.download_button("下载竞品 CSV", Path(csv_path).read_bytes(), file_name=Path(csv_path).name)
        st.download_button("下载竞品 Markdown", Path(md_path).read_text(encoding="utf-8"), file_name=Path(md_path).name)


def history_page() -> None:
    """Render historical markdown reports."""
    st.title("历史报告")
    report_dir = PROJECT_ROOT / "outputs" / "reports"
    files = sorted(report_dir.glob("*.md"), reverse=True)
    if not files:
        st.info("暂无历史报告。完成一次分析后会自动保存 Markdown 报告。")
        return
    for file in files:
        with st.expander(file.name):
            content = file.read_text(encoding="utf-8")
            st.download_button("下载", content, file_name=file.name, key=file.name)
            st.markdown(content)


def about_page() -> None:
    """Render project description."""
    st.title("关于项目")
    st.markdown(
        """
Steam Game Insight Copilot 是一个面向游戏策划、运营、用户研究和竞品分析的 Streamlit 工具。它把 Steam 玩家评论自动转化为清洗数据、关键词、反馈主题、游玩时长 × 推荐率位置和 Markdown 报告。

**数据来源说明**：数据来自 Steam 商店公开评论接口，仅保留评论内容和必要统计字段，不保存 steamid 等不必要身份信息。

**合规说明**：工具用于学习、研究和个人作品集展示；请求间有延迟，避免高频访问；导出结果应遵守 Steam 相关服务条款。

**适合简历的项目亮点**：
- 用 AI 工作流提升信息收集、数据分析、方案整理和内容产出效率。
- 从玩家评论到反馈主题和游玩时长 × 推荐率位置，体现游戏行业业务理解。
- 支持无 API Key 本地运行，也预留 OpenAI 报告润色能力。
- 支持单款游戏分析、竞品对比、CSV/Markdown/ZIP 导出和 Demo 模式。
"""
    )


PAGES = {
    "单款游戏分析": single_game_page,
    "竞品对比分析": competitor_page,
    "历史报告": history_page,
    "关于项目": about_page,
}


def main() -> None:
    """Run Streamlit app."""
    page = st.sidebar.radio("功能导航", list(PAGES.keys()))
    PAGES[page]()


if __name__ == "__main__":
    main()
