import os
import re
from functools import lru_cache
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

MOVIE_COL = "title"
TEXT_COL = "review_clean"

# Hide noisy NER labels (improves perceived accuracy)
BAD_LABELS = {"CARDINAL", "ORDINAL", "QUANTITY", "PERCENT", "MONEY", "TIME", "DATE"}

# -------------------------
# Load dataset
# -------------------------
def clean_text(text: str) -> str:
    text = str(text)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def load_dataset() -> pd.DataFrame:
    """
    Tries:
      1) kagglehub dataset used in your notebook
      2) fallback: local CSVs in ./data/imdb_list.csv and ./data/imdb_reviews.csv
    Returns merged df containing title + review + rating columns.
    """
    try:
        import kagglehub
        from kagglehub import KaggleDatasetAdapter

        dataset_id = "shivvm/popular-movies-imdb-reviews-dataset"
        movies = kagglehub.load_dataset(KaggleDatasetAdapter.PANDAS, dataset_id, "imdb_list.csv")
        reviews = kagglehub.load_dataset(KaggleDatasetAdapter.PANDAS, dataset_id, "imdb_reviews.csv")

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
                " - OR place ./movie_review_site/data/imdb_list.csv and imdb_reviews.csv\n"
                f"Original error: {e}"
            )

        movies = pd.read_csv(movies_path)
        reviews = pd.read_csv(reviews_path)
        df = reviews.merge(movies, left_on="imdb_id", right_on="id", how="left")
        if "review_clean" not in df.columns and "review" in df.columns:
            df["review_clean"] = df["review"].astype(str).apply(clean_text)
        return df

# Load once at startup
df_all = load_dataset()

# -------------------------
# Local poster mapping (Option A)
# posters.csv format:
#   movie_id,poster_file
#   tt4154796,tt4154796.jpg
# Posters folder:
#   ./static/posters/<poster_file>
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
    """
    Try posters.csv key by movie_id first, then by title (optional fallback).
    """
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
        "poster", "poster_url", "poster_link", "image", "image_url", "img", "img_url",
        "cover", "cover_url", "thumbnail", "thumb", "photo"
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
        {initials.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")}
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
# spaCy setup (en_core_web_trf + movie-aware ruler)
# -------------------------
def _ensure_sentencizer(nlp):
    if "parser" not in nlp.pipe_names and "senter" not in nlp.pipe_names and "sentencizer" not in nlp.pipe_names:
        nlp.add_pipe("sentencizer", first=True)
    return nlp

def _try_load(path: str):
    try:
        return spacy.load(path)
    except Exception:
        return None

def _build_movie_ruler_patterns(df: pd.DataFrame, max_titles: int = 4000):
    patterns: List[Dict[str, Any]] = []

    if MOVIE_COL in df.columns:
        titles = (
            df[MOVIE_COL].dropna().astype(str).map(str.strip)
            .loc[lambda s: s.str.len().between(2, 80)]
            .drop_duplicates()
            .head(max_titles)
            .tolist()
        )
        patterns.extend({"label": "WORK_OF_ART", "pattern": t} for t in titles)

    # optional aliases (edit/remove)
    patterns += [
        {"label": "PERSON", "pattern": "Iron Man"},
        {"label": "PERSON", "pattern": "Tony Stark"},
        {"label": "PERSON", "pattern": "Steve Rogers"},
        {"label": "PERSON", "pattern": "Thanos"},
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

def _load_spacy_nlps(df: pd.DataFrame):
    custom_path = os.environ.get(
        "NER_MODEL_PATH",
        os.path.join(os.path.dirname(__file__), "ner_model", "model-best")
    )

    ner_base = spacy.load("en_core_web_trf")
    ner_base = _ensure_sentencizer(ner_base)
    ner_base = _add_movie_ruler(ner_base, df)

    ner_trained = _try_load(custom_path) or spacy.load("en_core_web_trf")
    ner_trained = _ensure_sentencizer(ner_trained)
    ner_trained = _add_movie_ruler(ner_trained, df)

    nlp_sent = spacy.blank("en")
    nlp_sent.add_pipe("sentencizer")

    return ner_trained, ner_base, nlp_sent

ner_trained, ner_base, nlp_sent = _load_spacy_nlps(df_all)

# -------------------------
# Summarization (fixed dedup logic)
# -------------------------
def split_sentences(text: str, min_len: int = 20) -> List[str]:
    doc = nlp_sent(str(text))
    sents = [s.text.strip() for s in doc.sents]
    return [s for s in sents if len(s) >= int(min_len)]

def extractive_summary(
    text: str,
    k: int = 3,
    min_sent_len: int = 20,
    dedup_threshold: float = 0.75
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
# NER helpers (filtered)
# -------------------------
def _doc_ents_to_json(doc) -> List[Dict[str, Any]]:
    return [{"text": e.text, "label": e.label_, "start": e.start_char, "end": e.end_char} for e in doc.ents]

def _filter_ents(ents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for e in ents:
        if e["label"] in BAD_LABELS:
            continue
        if len(str(e.get("text", "")).strip()) < 2:
            continue
        out.append(e)
    return out

def _merge_entities(list_a, list_b) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for e in list_a + list_b:
        key = (int(e["start"]), int(e["end"]), str(e["label"]))
        if key not in seen:
            seen.add(key)
            out.append(e)
    out.sort(key=lambda x: (int(x["start"]), int(x["end"])))
    return out

@lru_cache(maxsize=4096)
def _ner_packed(text: str) -> Tuple[Tuple[int, int, str, str], ...]:
    t = str(text)
    doc_t = ner_trained(t)
    doc_b = ner_base(t)
    ents = _merge_entities(
        _filter_ents(_doc_ents_to_json(doc_t)),
        _filter_ents(_doc_ents_to_json(doc_b)),
    )
    return tuple((int(e["start"]), int(e["end"]), str(e["label"]), str(e["text"])) for e in ents)

def ner_entities(text: str) -> List[Dict[str, Any]]:
    packed = _ner_packed(text)
    return [{"start": s, "end": e, "label": lab, "text": txt} for (s, e, lab, txt) in packed]

def ensure_min_entities(summary_text: str, ents_summary, ents_full, min_entities: int = 2):
    summary_text = str(summary_text)
    min_entities = int(min_entities)

    def uniq_count(ents):
        return len({(str(e.get("label")), str(e.get("text"))) for e in ents})

    if not summary_text.strip() or min_entities <= 0:
        return ents_summary

    out = list(ents_summary or [])
    if uniq_count(out) >= min_entities:
        return out

    for e in (ents_full or []):
        if uniq_count(out) >= min_entities:
            break

        t = str(e.get("text", "")).strip()
        lab = str(e.get("label", "")).strip()
        if len(t) < 2 or not lab:
            continue

        m = re.search(re.escape(t), summary_text, flags=re.IGNORECASE)
        if not m:
            continue

        out.append({"text": summary_text[m.start():m.end()], "label": lab, "start": m.start(), "end": m.end()})

    out.sort(key=lambda x: (int(x["start"]), int(x["end"])))
    return out

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
    min_entities: int = 2
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
    ents_summary = ensure_min_entities(summary_text, ents_summary, ents_full, min_entities=int(min_entities))

    return {
        "summary_sentences": summary_sents,
        "summary_text": summary_text,
        "entities_summary": ents_summary,
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

        out.append({
            "title": title,
            "year": str(r.get(year_col) or "").strip() if year_col else "",
            "movie_id": movie_id,
            "poster_url": poster,
            "genre": genre,
        })
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
