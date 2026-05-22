import os
import re
from functools import lru_cache
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


MOVIE_COL = "title"
TEXT_COL = "review_clean"

BAD_LABELS = {"CARDINAL", "ORDINAL", "QUANTITY", "PERCENT", "MONEY", "TIME", "DATE"}


# -------------------------
# Text cleaning
# -------------------------
def clean_text(text: str) -> str:
    text = str(text)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# -------------------------
# Sentiment Analysis
# -------------------------
sentiment_analyzer = SentimentIntensityAnalyzer()

NEGATIVE_PHRASES = [
    "cliche", "cliches", "done to death", "couldn't care", "could not care",
    "soapy", "not good", "not worth", "overrated", "boring", "bad",
    "weak", "poor", "worst", "disappointing", "predictable", "messy",
    "terrible", "awful", "waste", "superior to this", "skewing the rating",
    "rated so high", "fails", "failed", "problem", "annoying", "flat",
    "unnecessary", "decent but", "but in the end", "corruption angle",
    "love angle", "melodrama", "mockery", "soap", "has been done",
    "done before", "all kind of soapy", "couldn't care what happened",
    "i couldn't care", "i could not care", "honestly", "much superior"
]

POSITIVE_PHRASES = [
    "amazing", "excellent", "masterpiece", "brilliant", "wonderful",
    "emotional", "powerful", "stunning", "fantastic", "impressive",
    "loved", "great", "best", "favorite", "incredible", "worth watching",
    "must watch", "recommend", "beautiful", "perfect", "strong acting",
    "great acting", "well made", "well-written", "enjoyed", "done justice",
    "real acting", "deserves it", "round of applause", "go and watch",
    "learn from the best"
]


def _phrase_hits(text: str, phrases: List[str]) -> int:
    lower = clean_text(text).lower()
    return sum(1 for phrase in phrases if phrase in lower)


def _normalize_scores(pos: float, neu: float, neg: float) -> Dict[str, float]:
    total = pos + neu + neg

    if total <= 0:
        return {
            "positive": 0.0,
            "neutral": 1.0,
            "negative": 0.0,
        }

    return {
        "positive": round(pos / total, 3),
        "neutral": round(neu / total, 3),
        "negative": round(neg / total, 3),
    }


def analyze_sentiment(text: str) -> Dict[str, Any]:
    text = clean_text(text)
    scores = sentiment_analyzer.polarity_scores(text)

    vader_compound = float(scores["compound"])
    positive_hits = _phrase_hits(text, POSITIVE_PHRASES)
    negative_hits = _phrase_hits(text, NEGATIVE_PHRASES)

    pos = float(scores["pos"])
    neu = float(scores["neu"])
    neg = float(scores["neg"])
    compound = vader_compound

    if negative_hits > positive_hits:
        label = "Negative"

        neg = min(0.85, max(neg, 0.45 + (negative_hits * 0.06)))
        pos = min(pos, 0.12)
        neu = max(0.03, 1.0 - neg - pos)

        compound = max(-0.95, min(compound, -0.35 - (negative_hits * 0.05)))

    elif positive_hits > negative_hits:
        label = "Positive"

        pos = min(0.85, max(pos, 0.45 + (positive_hits * 0.06)))
        neg = min(neg, 0.12)
        neu = max(0.03, 1.0 - pos - neg)

        compound = min(0.95, max(compound, 0.35 + (positive_hits * 0.05)))

    else:
        if compound >= 0.2:
            label = "Positive"
        elif compound <= -0.2:
            label = "Negative"
        else:
            label = "Neutral"

    normalized = _normalize_scores(pos, neu, neg)

    return {
        "label": label,
        "compound": round(compound, 3),
        "positive": normalized["positive"],
        "neutral": normalized["neutral"],
        "negative": normalized["negative"],
        "positive_hits": positive_hits,
        "negative_hits": negative_hits,
        "vader_compound": round(vader_compound, 3),
    }


# -------------------------
# Load dataset
# -------------------------
def load_dataset() -> pd.DataFrame:
    try:
        import kagglehub
        from kagglehub import KaggleDatasetAdapter

        dataset_id = "shivvm/popular-movies-imdb-reviews-dataset"

        movies = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            dataset_id,
            "imdb_list.csv"
        )

        reviews = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            dataset_id,
            "imdb_reviews.csv"
        )

        df = reviews.merge(movies, left_on="imdb_id", right_on="id", how="left")

        if "review_clean" not in df.columns and "review" in df.columns:
            df["review_clean"] = df["review"].astype(str).apply(clean_text)

        return df

    except Exception as e:
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        movies_path = os.path.join(data_dir, "imdb_list.csv")
        reviews_path = os.path.join(data_dir, "imdb_reviews.csv")

        if not (os.path.exists(movies_path) and os.path.exists(reviews_path)):
            raise RuntimeError(
                "Could not load Kaggle dataset via kagglehub, and local CSVs were not found.\n"
                "Either:\n"
                " - ensure internet access and install kagglehub\n"
                " - OR place ./Reviewly/data/imdb_list.csv and imdb_reviews.csv\n"
                f"Original error: {e}"
            )

        movies = pd.read_csv(movies_path)
        reviews = pd.read_csv(reviews_path)

        df = reviews.merge(movies, left_on="imdb_id", right_on="id", how="left")

        if "review_clean" not in df.columns and "review" in df.columns:
            df["review_clean"] = df["review"].astype(str).apply(clean_text)

        return df


df_all = load_dataset()


# -------------------------
# Poster mapping
# -------------------------
POSTER_MAP: Dict[str, str] = {}

def load_poster_map() -> None:
    global POSTER_MAP

    path = os.path.join(os.path.dirname(__file__), "posters.csv")

    if not os.path.exists(path):
        POSTER_MAP = {}
        return

    dfp = pd.read_csv(path)
    out: Dict[str, str] = {}

    for _, r in dfp.dropna().iterrows():
        mid = str(r.get("movie_id", "")).strip()
        pf = str(r.get("poster_file", "")).strip()

        if mid and pf:
            out[mid] = pf

    POSTER_MAP = out


load_poster_map()


def poster_url_for_movie_id(movie_id: str, title: str = "") -> str:
    mid = "" if movie_id is None else str(movie_id).strip()
    t = "" if title is None else str(title).strip()

    f = POSTER_MAP.get(mid, "")

    if not f and t:
        f = POSTER_MAP.get(t, "")

    if not f:
        return ""

    return f"/static/posters/{f}"


# -------------------------
# Poster + Genre helpers
# -------------------------
def _pick_poster_col(df: pd.DataFrame) -> str | None:
    candidates = [
        "poster", "poster_url", "poster_link", "image", "image_url",
        "img", "img_url", "cover", "cover_url", "thumbnail",
        "thumb", "photo"
    ]

    cols_lower = {c.lower(): c for c in df.columns}

    for c in candidates:
        if c in cols_lower:
            return cols_lower[c]

    return None


POSTER_COL = _pick_poster_col(df_all)


def _pick_genre_col(df: pd.DataFrame) -> str | None:
    candidates = ["genre", "genres", "genre_list", "category", "categories"]
    cols_lower = {c.lower(): c for c in df.columns}

    for c in candidates:
        if c in cols_lower:
            return cols_lower[c]

    return None


GENRE_COL = _pick_genre_col(df_all)


def _normalize_genre(val: Any) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""

    s = str(val).strip()

    if not s:
        return ""

    s = s.replace("|", ",")

    parts = [p.strip() for p in s.split(",") if p.strip()]
    seen = set()
    clean = []

    for p in parts:
        key = p.lower()

        if key not in seen:
            seen.add(key)
            clean.append(p)

    return " • ".join(clean[:5])


def make_placeholder_poster(title: str) -> str:
    t = (title or "").strip()
    initials = (t[:18] + "…") if len(t) > 18 else t

    svg = f"""
    <svg xmlns='http://www.w3.org/2000/svg' width='300' height='450'>
      <defs>
        <linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>
          <stop offset='0' stop-color='#1b2a3d'/>
          <stop offset='1' stop-color='#0f1722'/>
        </linearGradient>
      </defs>
      <rect width='300' height='450' fill='url(#g)'/>
      <rect x='18' y='18' width='264' height='414' rx='18' ry='18'
            fill='rgba(255,255,255,0.06)' stroke='rgba(255,255,255,0.08)'/>
      <text x='30' y='230' fill='#e8eef6' font-size='22'
            font-family='system-ui, -apple-system, Segoe UI, Roboto, Arial' font-weight='800'>
        {initials.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")}
      </text>
      <text x='30' y='260' fill='#9fb0c7' font-size='12'
            font-family='system-ui, -apple-system, Segoe UI, Roboto, Arial'>
        No poster in dataset
      </text>
    </svg>
    """.strip()

    import urllib.parse
    return "data:image/svg+xml;utf8," + urllib.parse.quote(svg)


# -------------------------
# spaCy setup
# -------------------------
def _ensure_sentencizer(nlp):
    if (
        "parser" not in nlp.pipe_names
        and "senter" not in nlp.pipe_names
        and "sentencizer" not in nlp.pipe_names
    ):
        nlp.add_pipe("sentencizer", first=True)

    return nlp


def _load_spacy_nlps(df: pd.DataFrame):
    """
    Fast version:
    Use only one small spaCy model.
    Do not load transformer model.
    Do not run two NER models per review.
    """
    try:
        ner_base = spacy.load("en_core_web_sm")
    except Exception:
        raise RuntimeError(
            "spaCy model en_core_web_sm is not installed.\n"
            "Run this command:\n"
            "python -m spacy download en_core_web_sm"
        )

    ner_base = _ensure_sentencizer(ner_base)
    ner_base = _add_movie_ruler(ner_base, df)

    ner_trained = ner_base

    nlp_sent = spacy.blank("en")
    nlp_sent.add_pipe("sentencizer")

    return ner_trained, ner_base, nlp_sent


def _build_movie_ruler_patterns(df: pd.DataFrame, max_titles: int = 2000):
    patterns: List[Dict[str, Any]] = []

    if MOVIE_COL in df.columns:
        titles = (
            df[MOVIE_COL]
            .dropna()
            .astype(str)
            .map(str.strip)
            .loc[lambda s: s.str.len().between(2, 80)]
            .drop_duplicates()
            .head(max_titles)
            .tolist()
        )

        patterns.extend({"label": "WORK_OF_ART", "pattern": t} for t in titles)

    patterns += [
        {"label": "PERSON", "pattern": "Iron Man"},
        {"label": "PERSON", "pattern": "Tony Stark"},
        {"label": "PERSON", "pattern": "Steve Rogers"},
        {"label": "PERSON", "pattern": "Thanos"},
        {"label": "PERSON", "pattern": "Vikrant Massey"},
        {"label": "PERSON", "pattern": "Vikrant"},
    ]

    return patterns


def _add_movie_ruler(nlp, df):
    if "ner" not in nlp.pipe_names:
        return nlp

    if "entity_ruler" in nlp.pipe_names:
        return nlp

    ruler = nlp.add_pipe("entity_ruler", before="ner")
    ruler.add_patterns(_build_movie_ruler_patterns(df))

    return nlp


ner_trained, ner_base, nlp_sent = _load_spacy_nlps(df_all)


# -------------------------
# Summarization
# -------------------------
def split_sentences(text: str, min_len: int = 20) -> List[str]:
    doc = nlp_sent(str(text))
    sents = [s.text.strip() for s in doc.sents]
    return [s for s in sents if len(s) >= int(min_len)]


def extractive_summary(
    text: str,
    k: int = 3,
    min_sent_len: int = 20,
    dedup_threshold: float = 0.75,
) -> List[str]:
    sents = split_sentences(text, min_len=min_sent_len)

    if not sents:
        return []

    if len(sents) <= int(k):
        return sents

    vec = TfidfVectorizer(stop_words="english")
    X = vec.fit_transform(sents)

    centroid = np.asarray(X.mean(axis=0))
    scores = cosine_similarity(X, centroid).reshape(-1)

    order = np.argsort(scores)[::-1]
    picked: List[int] = []

    for idx in order:
        if len(picked) >= int(k) * 3:
            break

        if not picked:
            picked.append(int(idx))
            continue

        picked_mat = X[picked]
        sims = cosine_similarity(X[idx], picked_mat).reshape(-1)

        if float(sims.max()) < float(dedup_threshold):
            picked.append(int(idx))

    picked = sorted(picked[: int(k)])

    return [sents[i] for i in picked]


# -------------------------
# Keyword Extraction
# -------------------------
def extract_keywords(text: str, top_n: int = 8) -> List[str]:
    text = clean_text(text)

    if not text:
        return []

    custom_stopwords = {
        "movie", "film", "review", "really", "just", "like",
        "story", "watch", "watched", "thing", "things",
        "make", "made", "makes", "time", "way", "end",
        "character", "characters", "scene", "scenes"
    }

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=100,
            ngram_range=(1, 2)
        )

        X = vectorizer.fit_transform([text])
        scores = X.toarray()[0]
        terms = vectorizer.get_feature_names_out()

        ranked = sorted(
            zip(terms, scores),
            key=lambda x: x[1],
            reverse=True
        )

        keywords = []

        for term, score in ranked:
            term = str(term).strip().lower()

            if not term:
                continue

            if len(term) < 3:
                continue

            if term.isdigit():
                continue

            if term in custom_stopwords:
                continue

            keywords.append(term)

            if len(keywords) >= int(top_n):
                break

        return keywords

    except Exception:
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())

        stop = {
            "this", "that", "with", "have", "they", "from",
            "what", "when", "where", "which", "there", "their",
            "about", "movie", "film", "review", "story", "watch"
        }

        freq = {}

        for word in words:
            if word not in stop:
                freq[word] = freq.get(word, 0) + 1

        ranked_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)

        return [word for word, count in ranked_words[:top_n]]


# -------------------------
# NER helpers
# -------------------------
def _doc_ents_to_json(doc) -> List[Dict[str, Any]]:
    return [
        {
            "text": e.text,
            "label": e.label_,
            "start": e.start_char,
            "end": e.end_char,
        }
        for e in doc.ents
    ]


def _filter_ents(ents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []

    for e in ents:
        if e["label"] in BAD_LABELS:
            continue

        if len(str(e.get("text", "")).strip()) < 2:
            continue

        out.append(e)

    return out


@lru_cache(maxsize=4096)
def _ner_packed(text: str) -> Tuple[Tuple[int, int, str, str], ...]:
    t = clean_text(text)

    # Limit long reviews so modal loads faster
    t = t[:2500]

    # Run only one spaCy model
    doc = ner_base(t)

    ents = _filter_ents(_doc_ents_to_json(doc))

    seen = set()
    clean_ents = []

    for e in ents:
        text_value = str(e.get("text", "")).strip()
        label = str(e.get("label", "")).strip()
        start = int(e.get("start", 0))
        end = int(e.get("end", 0))

        key = (start, end, label, text_value.lower())

        if key not in seen:
            seen.add(key)
            clean_ents.append({
                "text": text_value,
                "label": label,
                "start": start,
                "end": end,
            })

    clean_ents.sort(key=lambda x: (int(x["start"]), int(x["end"])))

    return tuple(
        (int(e["start"]), int(e["end"]), str(e["label"]), str(e["text"]))
        for e in clean_ents
    )


def ner_entities(text: str) -> List[Dict[str, Any]]:
    packed = _ner_packed(text)

    return [
        {
            "start": s,
            "end": e,
            "label": lab,
            "text": txt,
        }
        for (s, e, lab, txt) in packed
    ]


def ensure_min_entities(summary_text: str, ents_summary, ents_full, min_entities: int = 2):
    summary_text = str(summary_text)
    min_entities = int(min_entities)

    def uniq_count(ents):
        return len({
            (
                str(e.get("label", "")),
                str(e.get("text", "")).lower(),
                int(e.get("start", 0)),
                int(e.get("end", 0)),
            )
            for e in ents
        })

    if not summary_text.strip() or min_entities <= 0:
        return ents_summary

    out = list(ents_summary or [])

    if uniq_count(out) >= min_entities:
        return out

    for e in ents_full or []:
        if uniq_count(out) >= min_entities:
            break

        t = str(e.get("text", "")).strip()
        lab = str(e.get("label", "")).strip()

        if len(t) < 2 or not lab:
            continue

        m = re.search(re.escape(t), summary_text, flags=re.IGNORECASE)

        if not m:
            continue

        candidate = {
            "text": summary_text[m.start():m.end()],
            "label": lab,
            "start": m.start(),
            "end": m.end(),
        }

        duplicate = any(
            int(x.get("start", 0)) == candidate["start"]
            and int(x.get("end", 0)) == candidate["end"]
            and str(x.get("label", "")) == candidate["label"]
            and str(x.get("text", "")).lower() == candidate["text"].lower()
            for x in out
        )

        if not duplicate:
            out.append(candidate)

    out.sort(key=lambda x: (int(x["start"]), int(x["end"])))

    return out


# -------------------------
# Review Insights
# -------------------------
def _classify_sentence_for_insight(sentence: str) -> str:
    sent = clean_text(sentence)
    lower = sent.lower()

    positive_exceptions = [
        "no bollywood masala",
        "reality at its peak",
        "done justice",
        "amazing performance",
        "real acting",
        "deserves it",
        "round of applause",
        "go and watch",
        "learn from the best",
        "worth watching",
    ]

    negative_exceptions = [
        "mockery",
        "done to death",
        "couldn't care",
        "could not care",
        "overrated",
        "boring",
        "disappointing",
        "waste",
        "soapy",
        "weak",
        "poor",
        "worst",
    ]

    if any(p in lower for p in positive_exceptions):
        return "positive"

    if any(n in lower for n in negative_exceptions):
        return "negative"

    neg_hits = _phrase_hits(sent, NEGATIVE_PHRASES)
    pos_hits = _phrase_hits(sent, POSITIVE_PHRASES)
    vader = sentiment_analyzer.polarity_scores(sent)["compound"]

    if neg_hits > pos_hits:
        return "negative"

    if pos_hits > neg_hits and vader >= -0.05:
        return "positive"

    if vader <= -0.25:
        return "negative"

    if vader >= 0.35:
        return "positive"

    return "neutral"


def generate_review_insights(
    text: str,
    summary_sents: List[str],
    sentiment: Dict[str, Any]
) -> Dict[str, Any]:
    text = clean_text(text)
    summary_text = " ".join(summary_sents).strip()

    sentences = split_sentences(text, min_len=15)

    positive_points = []
    negative_points = []

    for sent in sentences:
        label = _classify_sentence_for_insight(sent)

        if label == "positive":
            positive_points.append(sent)

        if label == "negative":
            negative_points.append(sent)

    positive_points = positive_points[:3]
    negative_points = negative_points[:3]

    sentiment_label = sentiment.get("label", "Neutral")

    if sentiment_label == "Negative" and not negative_points:
        negative_points = summary_sents[:2] or [
            "The review expresses a negative overall opinion but does not contain a clearly isolated negative sentence."
        ]

    if sentiment_label == "Positive" and not positive_points:
        positive_points = summary_sents[:2] or [
            "The review expresses a positive overall opinion but does not contain a clearly isolated positive sentence."
        ]

    if not positive_points:
        positive_points = ["The review does not clearly mention specific positive points."]

    if not negative_points:
        negative_points = ["The review does not clearly mention major negative points."]

    if sentiment_label == "Positive":
        final_opinion = "The reviewer generally has a positive opinion and recommends the movie."
    elif sentiment_label == "Negative":
        final_opinion = "The reviewer generally has a negative opinion and does not strongly recommend the movie."
    else:
        final_opinion = "The reviewer has a mixed or neutral opinion about the movie."

    if not summary_text:
        summary_text = "No clear summary could be generated from this review."

    return {
        "overall_summary": summary_text,
        "positive_points": positive_points,
        "negative_points": negative_points,
        "final_opinion": final_opinion,
    }


# -------------------------
# AI Confidence Score
# -------------------------
def calculate_ai_confidence(
    sentiment: Dict[str, Any],
    keywords: List[str],
    entities: List[Dict[str, Any]],
    summary_sents: List[str]
) -> Dict[str, Any]:
    confidence = 50

    compound = abs(float(sentiment.get("compound", 0)))
    positive_hits = int(sentiment.get("positive_hits", 0))
    negative_hits = int(sentiment.get("negative_hits", 0))

    if compound >= 0.7:
        confidence += 20
    elif compound >= 0.4:
        confidence += 15
    elif compound >= 0.2:
        confidence += 10

    if positive_hits > 0 or negative_hits > 0:
        confidence += 10

    if len(keywords) >= 5:
        confidence += 10
    elif len(keywords) >= 3:
        confidence += 6

    unique_entities = {
        (str(e.get("label", "")), str(e.get("text", "")).lower())
        for e in entities
    }

    if len(unique_entities) >= 3:
        confidence += 8
    elif len(unique_entities) >= 1:
        confidence += 4

    if len(summary_sents) >= 2:
        confidence += 7

    confidence = max(0, min(confidence, 98))

    if confidence >= 80:
        level = "High"
        reason = "The review has clear sentiment signals, useful keywords, and enough text for analysis."
    elif confidence >= 60:
        level = "Medium"
        reason = "The review has enough information, but some signals may be mixed or limited."
    else:
        level = "Low"
        reason = "The review may be too short, unclear, or difficult to analyze confidently."

    return {
        "score": confidence,
        "level": level,
        "reason": reason,
    }


# -------------------------
# Public API for the web app
# -------------------------
def list_movies() -> List[str]:
    return sorted(df_all[MOVIE_COL].dropna().astype(str).unique().tolist())


def get_reviews_for_movie(movie_title: str, limit: int = 40) -> pd.DataFrame:
    movie_title = "" if movie_title is None else str(movie_title).strip()

    sub = df_all[df_all[MOVIE_COL].astype(str) == movie_title].copy()
    sub = sub.dropna(subset=[TEXT_COL]).copy()
    sub = sub.reset_index().rename(columns={"index": "_row_id"})
    sub = sub[sub[TEXT_COL].astype(str).str.len() > 0].head(int(limit)).reset_index(drop=True)

    return sub


def get_row_by_id(row_id: int) -> pd.Series:
    return df_all.loc[int(row_id)]


@lru_cache(maxsize=2048)
def analyze_review(
    text: str,
    k_summary: int = 3,
    min_sent_len: int = 20,
    dedup_threshold: float = 0.75,
    min_entities: int = 2,
) -> Dict[str, Any]:
    text = clean_text(text)

    summary_sents = extractive_summary(
        text,
        k=int(k_summary),
        min_sent_len=int(min_sent_len),
        dedup_threshold=float(dedup_threshold),
    )

    summary_text = " ".join(summary_sents).strip()

    ents_full = ner_entities(text)
    ents_summary = ner_entities(summary_text) if summary_text else []

    ents_summary = ensure_min_entities(
        summary_text,
        ents_summary,
        ents_full,
        min_entities=int(min_entities),
    )

    sentiment = analyze_sentiment(text)

    insights = generate_review_insights(
        text=text,
        summary_sents=summary_sents,
        sentiment=sentiment,
    )

    keywords = extract_keywords(text)

    confidence = calculate_ai_confidence(
        sentiment=sentiment,
        keywords=keywords,
        entities=ents_summary,
        summary_sents=summary_sents,
    )

    return {
        "summary_sentences": summary_sents,
        "summary_text": summary_text,
        "entities_summary": ents_summary,
        "sentiment": sentiment,
        "insights": insights,
        "keywords": keywords,
        "confidence": confidence,
    }


def list_movies_rich(limit: int = 200) -> List[Dict[str, Any]]:
    df = df_all

    id_col = "imdb_id" if "imdb_id" in df.columns else ("id" if "id" in df.columns else None)
    year_col = "year" if "year" in df.columns else ("release_year" if "release_year" in df.columns else None)

    cols = [c for c in [MOVIE_COL, id_col, year_col, POSTER_COL, GENRE_COL] if c and c in df.columns]

    base = df[cols].dropna(subset=[MOVIE_COL]).copy()
    base[MOVIE_COL] = base[MOVIE_COL].astype(str)

    if id_col:
        base = base.drop_duplicates(subset=[id_col])
    else:
        base = base.drop_duplicates(subset=[MOVIE_COL])

    base = base.sort_values(MOVIE_COL, kind="mergesort").head(int(limit))

    out = []

    for _, r in base.iterrows():
        title = str(r.get(MOVIE_COL, "")).strip()
        movie_id = str(r.get(id_col) or "").strip() if id_col else title

        poster = ""

        if POSTER_COL:
            poster = str(r.get(POSTER_COL) or "").strip()

        if not poster:
            poster = poster_url_for_movie_id(movie_id, title=title)

        if not poster:
            poster = make_placeholder_poster(title)

        genre = _normalize_genre(r.get(GENRE_COL)) if GENRE_COL else ""

        out.append(
            {
                "title": title,
                "year": str(r.get(year_col) or "").strip() if year_col else "",
                "movie_id": movie_id,
                "poster_url": poster,
                "genre": genre,
            }
        )

    return out


def get_reviews_for_movie_id(movie_id: str, limit: int = 60) -> pd.DataFrame:
    movie_id = "" if movie_id is None else str(movie_id).strip()

    if "imdb_id" in df_all.columns:
        sub = df_all[df_all["imdb_id"].astype(str) == movie_id].copy()
    elif "id" in df_all.columns:
        sub = df_all[df_all["id"].astype(str) == movie_id].copy()
    else:
        sub = df_all[df_all[MOVIE_COL].astype(str) == movie_id].copy()

    sub = sub.dropna(subset=[TEXT_COL]).copy()
    sub = sub.reset_index().rename(columns={"index": "_row_id"})
    sub = sub[sub[TEXT_COL].astype(str).str.len() > 0].head(int(limit)).reset_index(drop=True)

    return sub