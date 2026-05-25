"""Statistical analysis and keyword extraction."""

from __future__ import annotations

import re
from collections import Counter

import jieba
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer


ZH_STOPWORDS = {
    "的", "了", "和", "是", "我", "也", "就", "都", "很", "还", "在", "有", "不", "这", "一个",
    "游戏", "真的", "但是", "就是", "可以", "感觉", "没有", "比较", "还是", "玩家", "这个",
    "自己", "一起", "朋友", "两个", "全部", "因为", "容易", "适合", "根本", "东西", "时候",
    "觉得", "有点", "不是", "不能", "不会", "一下", "现在", "已经", "还有", "如果", "然后",
    "里面", "出来", "问题", "一次", "很多", "这么", "那么", "非常", "特别", "建议", "希望",
    "来说", "这种", "直接", "可能", "需要", "之后", "之前", "目前", "虽然", "不过",
}
EN_STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "game", "very", "really", "have", "has",
    "but", "not", "you", "are", "was", "steam", "play", "player", "players",
}
POSITIVE_MODIFIERS = {
    "爽", "好玩", "有趣", "优秀", "舒服", "流畅", "上头", "丰富", "耐玩", "稳定", "清楚", "惊喜",
    "不错", "喜欢", "棒", "值", "便宜", "精致", "独特", "优秀", "推荐", "addictive", "great",
    "good", "excellent", "fun", "smooth", "polished", "worth", "cheap", "replayable", "amazing",
}
NEGATIVE_MODIFIERS = {
    "差", "糟糕", "无聊", "重复", "卡顿", "掉帧", "崩溃", "闪退", "报错", "太强", "太弱",
    "贵", "劝退", "看不懂", "不值", "不足", "粗糙", "难受", "失望", "broken", "bad", "rough",
    "boring", "repetitive", "expensive", "confusing", "crash", "bug", "lag", "stutter", "useless",
}
BARE_SENTIMENT_TERMS = {
    "爽", "好玩", "有趣", "优秀", "舒服", "流畅", "上头", "丰富", "耐玩", "稳定", "清楚", "惊喜",
    "不错", "喜欢", "棒", "值", "便宜", "精致", "独特", "推荐", "addictive", "great", "good",
    "excellent", "fun", "smooth", "polished", "worth", "cheap", "replayable", "amazing", "差",
    "糟糕", "无聊", "重复", "卡顿", "掉帧", "崩溃", "闪退", "报错", "太强", "太弱", "贵",
    "劝退", "看不懂", "不值", "不足", "粗糙", "难受", "失望", "bad", "rough", "boring",
    "repetitive", "expensive", "confusing", "broken", "useless",
}


def basic_stats(df: pd.DataFrame) -> dict:
    """Calculate core review metrics."""
    total = int(len(df)) if df is not None else 0
    if total == 0:
        return {
            "total_reviews": 0,
            "positive_count": 0,
            "negative_count": 0,
            "positive_rate": 0.0,
            "avg_playtime_hours": 0.0,
            "median_playtime_hours": 0.0,
            "avg_review_length": 0.0,
        }
    positive = int((df["sentiment"] == "positive").sum())
    negative = int((df["sentiment"] == "negative").sum())
    return {
        "total_reviews": total,
        "positive_count": positive,
        "negative_count": negative,
        "positive_rate": positive / total,
        "avg_playtime_hours": float(df.get("playtime_hours", pd.Series([0])).mean()),
        "median_playtime_hours": float(df.get("playtime_hours", pd.Series([0])).median()),
        "avg_review_length": float(df.get("review_length", pd.Series([0])).mean()),
    }


def _has_chinese(text: str) -> bool:
    """Return whether text contains Chinese characters."""
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _tokenize_texts(texts: list[str], language: str) -> list[str]:
    """Tokenize texts with shared filtering rules."""
    joined = " ".join(texts)
    use_chinese = language == "schinese" or (language == "all" and _has_chinese(joined))
    if use_chinese:
        words = []
        for word in jieba.lcut(joined):
            token = word.strip().lower()
            if len(token) >= 2 and token not in ZH_STOPWORDS and not re.fullmatch(r"\W+", token):
                words.append(token)
        return words

    tokens = re.findall(r"(?u)\b[a-zA-Z][a-zA-Z]{2,}\b", joined.lower())
    return [token for token in tokens if token not in EN_STOPWORDS]


def _collect_texts(df: pd.DataFrame, text_col: str) -> list[str]:
    """Collect non-empty text values from a DataFrame."""
    if df is None or df.empty or text_col not in df.columns:
        return []
    return [str(x) for x in df[text_col].dropna().tolist() if str(x).strip()]


def _join_phrase(tokens: list[str]) -> str:
    """Join phrase tokens with spaces when Latin words are involved."""
    if any(re.search(r"[a-zA-Z]", token) for token in tokens):
        return " ".join(tokens)
    return "".join(tokens)


def extract_keywords(
    df: pd.DataFrame,
    text_col: str = "review_clean",
    language: str = "schinese",
    top_n: int = 30,
) -> list[tuple[str, int]]:
    """Extract frequent keywords from review text."""
    texts = _collect_texts(df, text_col)
    if not texts:
        return []
    if language == "schinese" or (language == "all" and _has_chinese(" ".join(texts))):
        return Counter(_tokenize_texts(texts, language)).most_common(top_n)

    vectorizer = CountVectorizer(stop_words=list(EN_STOPWORDS), token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]{2,}\b")
    try:
        matrix = vectorizer.fit_transform(texts)
    except ValueError:
        return []
    counts = matrix.sum(axis=0).A1
    vocab = vectorizer.get_feature_names_out()
    pairs = sorted(zip(vocab, counts), key=lambda item: item[1], reverse=True)
    return [(word, int(count)) for word, count in pairs[:top_n]]


def extract_distinctive_keywords(
    target_df: pd.DataFrame,
    reference_df: pd.DataFrame,
    text_col: str = "review_clean",
    language: str = "schinese",
    top_n: int = 30,
) -> list[tuple[str, int]]:
    """Extract keywords that are frequent in target reviews and less common in reference reviews."""
    target_texts = _collect_texts(target_df, text_col)
    reference_texts = _collect_texts(reference_df, text_col)
    if not target_texts:
        return []

    target_counts = Counter(_tokenize_texts(target_texts, language))
    reference_counts = Counter(_tokenize_texts(reference_texts, language))
    if not target_counts:
        return []

    target_total = sum(target_counts.values()) or 1
    reference_total = sum(reference_counts.values()) or 1
    scored = []
    for word, count in target_counts.items():
        target_rate = count / target_total
        reference_rate = reference_counts.get(word, 0) / reference_total
        lift = target_rate / (reference_rate + 0.0005)
        score = count * lift
        scored.append((word, count, score))
    scored.sort(key=lambda item: (item[2], item[1]), reverse=True)
    return [(word, int(count)) for word, count, _ in scored[:top_n]]


def extract_sentiment_phrases(
    df: pd.DataFrame,
    text_col: str = "review_clean",
    language: str = "schinese",
    polarity: str = "positive",
    top_n: int = 30,
) -> list[tuple[str, int]]:
    """Extract sentiment-bearing phrases so outputs include modifiers instead of bare nouns."""
    texts = _collect_texts(df, text_col)
    if not texts:
        return []
    modifiers = POSITIVE_MODIFIERS if polarity == "positive" else NEGATIVE_MODIFIERS
    counts: Counter[str] = Counter()
    use_chinese = language == "schinese" or (language == "all" and _has_chinese(" ".join(texts)))

    for text in texts:
        if use_chinese:
            tokens = [token.strip().lower() for token in jieba.lcut(text) if token.strip()]
            tokens = [token for token in tokens if token not in ZH_STOPWORDS and not re.fullmatch(r"\W+", token)]
        else:
            tokens = re.findall(r"(?u)\b[a-zA-Z][a-zA-Z]{2,}\b", text.lower())
            tokens = [token for token in tokens if token not in EN_STOPWORDS]

        for idx, token in enumerate(tokens):
            if token not in modifiers:
                continue
            candidates = [token] if token in BARE_SENTIMENT_TERMS else []
            if idx > 0:
                candidates.append(_join_phrase([tokens[idx - 1], token]))
            if idx + 1 < len(tokens):
                candidates.append(_join_phrase([token, tokens[idx + 1]]))
            if idx > 0 and idx + 1 < len(tokens):
                candidates.append(_join_phrase([tokens[idx - 1], token, tokens[idx + 1]]))
            for phrase in candidates:
                if len(phrase.replace(" ", "")) >= 2:
                    counts[phrase] += 1

    return counts.most_common(top_n)


def get_top_helpful_reviews(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return the most helpful reviews by votes and weighted score."""
    if df is None or df.empty:
        return pd.DataFrame()
    sortable = df.copy()
    sortable["votes_up"] = pd.to_numeric(sortable.get("votes_up", 0), errors="coerce").fillna(0)
    sortable["weighted_vote_score"] = pd.to_numeric(sortable.get("weighted_vote_score", 0), errors="coerce").fillna(0)
    return sortable.sort_values(["votes_up", "weighted_vote_score"], ascending=False).head(n)
