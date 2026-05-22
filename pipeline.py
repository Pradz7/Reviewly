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

BAD_LABELS = {
    "CARDINAL", "ORDINAL", "QUANTITY", "PERCENT", "MONEY", "TIME", "DATE",
    "PRODUCT", "LAW", "LANGUAGE"
}

AMBIGUOUS_MOVIE_TITLES = {
    "it", "its", "us", "her", "up", "saw", "sing", "cars", "old", "fresh",
    "home", "life", "room", "split", "mother", "nope", "what", "open",
    "close", "run", "go", "big", "small", "yes", "no"
}

BLOCKED_ENTITY_WORDS = {
    "it", "its", "they", "them", "he", "she", "him", "her", "his", "hers",
    "we", "you", "your", "i", "me", "my", "mine", "our", "ours", "their",
    "theirs", "this", "that", "these", "those", "what", "whattt", "whatttt",
    "whattttt", "huh", "yeah", "wow", "lol", "haha", "okay", "ok", "nope",
    "yes", "no", "maybe", "thing", "stuff",

    "open", "opened", "opening", "close", "closed", "closing", "start",
    "started", "starting", "enter", "entered", "entering", "leave", "left",
    "run", "runs", "running", "hide", "hiding", "ask", "asked", "asking",
    "go", "goes", "going", "went", "know", "knowing", "think", "thinking",

    "door", "garage", "building", "shelter", "trail", "car", "beast",
    "thing", "stuff"
}

ACTOR_NAMES = {
    "leonardo dicaprio", "kate winslet", "christopher nolan", "cillian murphy",
    "robert pattinson", "margot robbie", "ryan gosling", "florence pugh",
    "timothee chalamet", "timothée chalamet", "zendaya", "tom hardy",
    "christian bale", "heath ledger", "joaquin phoenix", "anne hathaway",
    "matt damon", "benedict cumberbatch", "sam mendes", "george mackay",
    "dean-charles chapman", "vikrant massey", "vidhu vinod chopra",
    "irfan khan", "amitabh bachchan", "shah rukh khan", "aamir khan",
    "salman khan", "deepika padukone", "alia bhatt", "ranbir kapoor",
    "song kang ho", "choi woo shik", "park so dam", "bong joon ho",
    "tom hanks", "meryl streep", "brad pitt", "angelina jolie",
    "keanu reeves", "laurence fishburne", "carrie-anne moss",
    "emma stone", "andrew garfield", "tobey maguire", "daniel radcliffe",
    "emma watson", "rupert grint", "jennifer lawrence", "josh hutcherson",
    "daisy ridley", "adam driver", "harrison ford", "mark hamill",
    "natalie portman", "denzel washington", "morgan freeman",
    "anthony hopkins", "jodie foster", "sigourney weaver"
}

CHARACTER_NAMES = {
    "jack dawson", "rose dewitt bukater", "oppenheimer", "j robert oppenheimer",
    "barbie", "ken", "batman", "bruce wayne", "joker", "arthur fleck",
    "paul atreides", "chani", "frodo baggins", "gandalf", "aragorn",
    "harry potter", "hermione granger", "ron weasley", "voldemort",
    "luke skywalker", "darth vader", "princess leia", "han solo",
    "neo", "trinity", "morpheus", "john wick", "james bond",
    "katniss everdeen", "peeta mellark", "forrest gump", "hannibal lecter",
    "clarice starling", "ellen ripley", "indiana jones", "rocky balboa",
    "vito corleone", "michael corleone", "tyler durden", "amelie",
    "tony montana", "travis bickle", "simba", "mufasa", "woody", "buzz lightyear"
}

REVIEW_ASPECT_TERMS = {
    "story": "ASPECT",
    "storyline": "ASPECT",
    "plot": "ASPECT",
    "ending": "ASPECT",
    "beginning": "ASPECT",
    "middle": "ASPECT",
    "pacing": "ASPECT",
    "pace": "ASPECT",
    "acting": "ASPECT",
    "performance": "ASPECT",
    "performances": "ASPECT",
    "cast": "ASPECT",
    "character": "ASPECT",
    "characters": "ASPECT",
    "dialogue": "ASPECT",
    "dialogues": "ASPECT",
    "script": "ASPECT",
    "screenplay": "ASPECT",
    "direction": "ASPECT",
    "director": "ASPECT",
    "cinematography": "ASPECT",
    "visuals": "ASPECT",
    "visual effects": "ASPECT",
    "effects": "ASPECT",
    "vfx": "ASPECT",
    "soundtrack": "ASPECT",
    "music": "ASPECT",
    "score": "ASPECT",
    "sound": "ASPECT",
    "tension": "ASPECT",
    "suspense": "ASPECT",
    "emotion": "ASPECT",
    "emotional": "ASPECT",
    "comedy": "ASPECT",
    "humor": "ASPECT",
    "action": "ASPECT",
    "fight": "ASPECT",
    "war": "ASPECT",
    "aliens": "ASPECT",
    "alien": "ASPECT",
    "monster": "ASPECT",
    "meteor": "ASPECT",
    "space": "ASPECT",
    "dinosaur": "ASPECT",
    "dinosaurs": "ASPECT",
    "film": "ASPECT",
    "movie": "ASPECT",
    "sequel": "ASPECT",
    "prequel": "ASPECT",
    "climax": "ASPECT",
    "twist": "ASPECT",
    "theme": "ASPECT",
    "message": "ASPECT",
    "experience": "ASPECT",
}

LABEL_MAP = {
    "PERSON": "PERSON",
    "ORG": "ORGANIZATION",
    "GPE": "LOCATION",
    "LOC": "LOCATION",
    "NORP": "GROUP",
    "FAC": "LOCATION",
    "WORK_OF_ART": "MOVIE_TITLE",
    "MOVIE_TITLE": "MOVIE_TITLE",
    "ACTOR": "ACTOR",
    "CHARACTER": "CHARACTER",
    "ASPECT": "ASPECT",
}


def clean_text(text: str) -> str:
    text = str(text)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def parse_rating_value(rating):
    if rating is None:
        return None

    s = str(rating).strip()
    if not s:
        return None

    s = s.replace("/10", "").replace("⭐", "").strip()

    match = re.search(r"\d+(?:\.\d+)?", s)
    if not match:
        return None

    try:
        value = float(match.group(0))
    except Exception:
        return None

    if value > 10:
        value = value / 10

    if value < 0 or value > 10:
        return None

    return value


def rating_to_compound(rating_value):
    if rating_value is None:
        return 0.0

    return clamp((float(rating_value) - 5.0) / 5.0, -1.0, 1.0)


def rating_to_label(rating_value):
    if rating_value is None:
        return None

    if rating_value >= 7.0:
        return "Positive"

    if rating_value >= 5.0:
        return "Mixed"

    return "Negative"


def is_stretched_word(text: str) -> bool:
    text = clean_text(text).lower()

    if len(text) < 4:
        return False

    if not re.fullmatch(r"[a-zA-Z]+", text):
        return False

    return bool(re.search(r"(.)\1{3,}", text))


def is_weak_entity_text(text: str) -> bool:
    text = clean_text(text)
    lower = text.lower()

    if not lower:
        return True

    if lower in BLOCKED_ENTITY_WORDS:
        return True

    if is_stretched_word(lower):
        return True

    if len(lower) <= 1:
        return True

    if re.fullmatch(r"[^\w]+", lower):
        return True

    return False


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
    "i couldn't care", "i could not care", "honestly", "much superior",
    "goes down hill", "down hill fast", "downhill fast", "ridiculousness",
    "ridiculous", "got worse", "just got worse", "almost leave the theater",
    "should have because", "that was so bad", "so bad", "plain terrible",
    "just plain terrible", "cannot save this flop", "flop", "ugh",
    "why do we need to accept", "unable to hit their target", "silly enough",
    "not silly enough", "laughing at the ridiculousness"
]

POSITIVE_PHRASES = [
    "amazing", "excellent", "masterpiece", "brilliant", "wonderful",
    "emotional", "powerful", "stunning", "fantastic", "impressive",
    "loved", "great", "best", "favorite", "incredible", "worth watching",
    "must watch", "recommend", "beautiful", "perfect", "strong acting",
    "great acting", "well made", "well-written", "enjoyed", "done justice",
    "real acting", "deserves it", "round of applause", "go and watch",
    "learn from the best", "classic", "good"
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


def analyze_sentiment(text: str, rating=None) -> Dict[str, Any]:
    text = clean_text(text)
    lower = text.lower()

    scores = sentiment_analyzer.polarity_scores(text)
    vader_compound = float(scores["compound"])

    positive_hits = _phrase_hits(text, POSITIVE_PHRASES)
    negative_hits = _phrase_hits(text, NEGATIVE_PHRASES)

    text_compound = vader_compound

    if positive_hits > negative_hits:
        text_compound += min(0.20, 0.05 * (positive_hits - negative_hits))

    if negative_hits > positive_hits:
        text_compound -= min(0.20, 0.05 * (negative_hits - positive_hits))

    horror_content_words = [
        "gruesome", "frightening", "disturbing", "scary", "scarred",
        "violent", "violence", "cannibal", "cannibalistic", "horror",
        "creepy", "brutal", "bloody", "terrifying", "gory"
    ]

    praise_words = [
        "good", "great", "remember", "recommend", "worth", "power",
        "classic", "well", "strong", "liked", "love", "loved", "enjoyed",
        "fan", "best"
    ]

    horror_count = sum(1 for word in horror_content_words if word in lower)
    praise_count = sum(1 for word in praise_words if word in lower)

    if horror_count >= 2 and praise_count >= 1:
        text_compound += 0.18

    text_compound = clamp(text_compound, -1.0, 1.0)

    rating_value = parse_rating_value(rating)
    rating_compound = rating_to_compound(rating_value)
    rating_label = rating_to_label(rating_value)

    if rating_value is not None:
        final_compound = (0.60 * text_compound) + (0.40 * rating_compound)
    else:
        final_compound = text_compound

    final_compound = clamp(final_compound, -1.0, 1.0)

    if rating_value is not None:
        if rating_label == "Positive":
            if text_compound <= -0.65 and negative_hits >= positive_hits + 2:
                label = "Mixed"
            else:
                label = "Positive"

        elif rating_label == "Negative":
            if text_compound >= 0.65 and positive_hits >= negative_hits + 2:
                label = "Mixed"
            else:
                label = "Negative"

        else:
            label = "Mixed"
    else:
        if final_compound >= 0.2:
            label = "Positive"
        elif final_compound <= -0.2:
            label = "Negative"
        else:
            label = "Mixed"

    strength = min(abs(final_compound), 1.0)

    if label == "Positive":
        positive = round(0.45 + (0.35 * strength), 3)
        negative = round(max(0.05, 0.18 - (0.10 * strength)), 3)
        neutral = round(max(0.05, 1.0 - positive - negative), 3)

    elif label == "Negative":
        negative = round(0.45 + (0.35 * strength), 3)
        positive = round(max(0.05, 0.18 - (0.10 * strength)), 3)
        neutral = round(max(0.05, 1.0 - positive - negative), 3)

    else:
        positive = round(0.25 + max(0.0, final_compound) * 0.10, 3)
        negative = round(0.25 + max(0.0, -final_compound) * 0.10, 3)
        neutral = round(max(0.30, 1.0 - positive - negative), 3)

        total = positive + neutral + negative
        positive = round(positive / total, 3)
        neutral = round(neutral / total, 3)
        negative = round(negative / total, 3)

    return {
        "label": label,
        "compound": round(final_compound, 3),
        "positive": positive,
        "neutral": neutral,
        "negative": negative,
        "positive_hits": positive_hits,
        "negative_hits": negative_hits,
        "vader_compound": round(vader_compound, 3),
        "text_compound": round(text_compound, 3),
        "rating_value": rating_value,
        "rating_label": rating_label,
    }


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


def _ensure_sentencizer(nlp):
    if (
        "parser" not in nlp.pipe_names
        and "senter" not in nlp.pipe_names
        and "sentencizer" not in nlp.pipe_names
    ):
        nlp.add_pipe("sentencizer", first=True)

    return nlp


def _build_movie_ruler_patterns(df: pd.DataFrame, max_titles: int = 1000):
    patterns: List[Dict[str, Any]] = []

    if MOVIE_COL in df.columns:
        titles = (
            df[MOVIE_COL]
            .dropna()
            .astype(str)
            .map(str.strip)
            .loc[lambda s: s.str.len().between(3, 80)]
            .drop_duplicates()
            .head(max_titles)
            .tolist()
        )

        for title in titles:
            title_clean = title.strip()
            title_lower = title_clean.lower()

            if title_lower in AMBIGUOUS_MOVIE_TITLES:
                continue

            if len(title_clean.split()) == 1 and len(title_clean) <= 3:
                continue

            patterns.append({
                "label": "MOVIE_TITLE",
                "pattern": title_clean
            })

    for actor in ACTOR_NAMES:
        patterns.append({
            "label": "ACTOR",
            "pattern": actor.title()
        })

    for character in CHARACTER_NAMES:
        patterns.append({
            "label": "CHARACTER",
            "pattern": character.title()
        })

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


ner_trained, ner_base, nlp_sent = _load_spacy_nlps(df_all)


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


def extract_keywords(text: str, top_n: int = 8) -> List[str]:
    text = clean_text(text)

    if not text:
        return []

    custom_stopwords = {
        "movie", "film", "review", "really", "just", "like",
        "thing", "things", "make", "made", "makes", "time", "way", "end"
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
            "about", "movie", "film", "review"
        }

        freq = {}

        for word in words:
            if word not in stop:
                freq[word] = freq.get(word, 0) + 1

        ranked_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)

        return [word for word, count in ranked_words[:top_n]]


def polish_entity_label(text: str, label: str, context: str = "") -> str:
    entity = clean_text(text).lower()
    context_lower = clean_text(context).lower()

    if not entity:
        return "IGNORE"

    if is_weak_entity_text(entity):
        return "IGNORE"

    if entity in ACTOR_NAMES:
        return "ACTOR"

    if entity in CHARACTER_NAMES:
        return "CHARACTER"

    actor_context_words = [
        "actor", "actress", "performance", "performed", "cast",
        "played by", "starring", "role by", "directed by", "director"
    ]

    if label == "PERSON" and any(word in context_lower for word in actor_context_words):
        return "ACTOR"

    character_context_words = [
        "character", "role", "villain", "hero", "protagonist",
        "main character", "fictional"
    ]

    if label == "PERSON" and any(word in context_lower for word in character_context_words):
        return "CHARACTER"

    if label in {"WORK_OF_ART", "MOVIE_TITLE"}:
        return "MOVIE_TITLE"

    return LABEL_MAP.get(label, label)


def _doc_ents_to_json(doc) -> List[Dict[str, Any]]:
    entities = []

    for e in doc.ents:
        context = ""

        try:
            context = e.sent.text
        except Exception:
            context = doc.text[max(0, e.start_char - 80): e.end_char + 80]

        polished_label = polish_entity_label(
            text=e.text,
            label=e.label_,
            context=context,
        )

        entities.append({
            "text": e.text,
            "label": polished_label,
            "original_label": e.label_,
            "start": e.start_char,
            "end": e.end_char,
        })

    return entities


def _filter_ents(ents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []

    for e in ents:
        text = str(e.get("text", "")).strip()
        label = str(e.get("label", "")).strip()
        text_lower = text.lower()

        if label == "IGNORE":
            continue

        if label in BAD_LABELS:
            continue

        if len(text) < 2:
            continue

        if is_weak_entity_text(text):
            continue

        if label in {"MOVIE_TITLE", "WORK_OF_ART"} and text_lower in AMBIGUOUS_MOVIE_TITLES:
            continue

        if label in {"PERSON", "ACTOR", "CHARACTER"}:
            if text.islower():
                continue

            if len(text_lower) <= 2:
                continue

        if len(text.split()) == 1 and text.islower() and label != "ASPECT":
            continue

        out.append(e)

    return out


def extract_review_aspects(text: str) -> List[Dict[str, Any]]:
    text = clean_text(text)
    found = []
    seen = set()

    terms = sorted(REVIEW_ASPECT_TERMS.keys(), key=len, reverse=True)

    for term in terms:
        pattern = r"\b" + re.escape(term) + r"\b"

        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            start = match.start()
            end = match.end()
            actual_text = text[start:end]
            key = (start, end, actual_text.lower())

            if key in seen:
                continue

            seen.add(key)

            found.append({
                "text": actual_text,
                "label": "ASPECT",
                "original_label": "ASPECT",
                "start": start,
                "end": end,
            })

    found.sort(key=lambda x: (int(x["start"]), int(x["end"])))

    return found


def merge_and_clean_entities(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    priority = {
        "ACTOR": 1,
        "CHARACTER": 1,
        "MOVIE_TITLE": 1,
        "LOCATION": 1,
        "ORGANIZATION": 1,
        "PERSON": 2,
        "GROUP": 2,
        "ASPECT": 3,
    }

    cleaned = _filter_ents(entities)
    cleaned.sort(key=lambda e: (
        int(e.get("start", 0)),
        priority.get(str(e.get("label", "")), 9),
        int(e.get("end", 0))
    ))

    final = []
    occupied_ranges = []

    for e in cleaned:
        start = int(e.get("start", 0))
        end = int(e.get("end", 0))
        text = str(e.get("text", "")).strip()

        if not text:
            continue

        overlap = False

        for os, oe in occupied_ranges:
            if start < oe and end > os:
                overlap = True
                break

        if overlap:
            continue

        final.append(e)
        occupied_ranges.append((start, end))

    final.sort(key=lambda x: (int(x["start"]), int(x["end"])))

    return final


@lru_cache(maxsize=4096)
def _ner_packed(text: str) -> Tuple[Tuple[int, int, str, str, str], ...]:
    t = clean_text(text)
    t = t[:2500]

    doc = ner_base(t)
    ner_ents = _doc_ents_to_json(doc)
    aspect_ents = extract_review_aspects(t)

    ents = merge_and_clean_entities(ner_ents + aspect_ents)

    seen = set()
    clean_ents = []

    for e in ents:
        text_value = str(e.get("text", "")).strip()
        label = str(e.get("label", "")).strip()
        original_label = str(e.get("original_label", label)).strip()
        start = int(e.get("start", 0))
        end = int(e.get("end", 0))

        key = (start, end, label, text_value.lower())

        if key not in seen:
            seen.add(key)
            clean_ents.append({
                "text": text_value,
                "label": label,
                "original_label": original_label,
                "start": start,
                "end": end,
            })

    clean_ents.sort(key=lambda x: (int(x["start"]), int(x["end"])))

    return tuple(
        (
            int(e["start"]),
            int(e["end"]),
            str(e["label"]),
            str(e["text"]),
            str(e["original_label"]),
        )
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
            "original_label": original_lab,
        }
        for (s, e, lab, txt, original_lab) in packed
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
            "original_label": str(e.get("original_label", lab)),
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


def _classify_sentence_for_insight(sentence: str) -> str:
    sent = clean_text(sentence)
    lower = sent.lower()

    if "?" in sent and any(word in lower for word in ["help", "huh", "why", "really"]):
        return "negative"

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
        "classic western",
        "star power",
        "long-time fan",
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
        "goes down hill",
        "down hill fast",
        "downhill fast",
        "ridiculousness",
        "ridiculous",
        "got worse",
        "just got worse",
        "almost leave the theater",
        "so bad",
        "plain terrible",
        "cannot save this flop",
        "flop",
        "ugh",
        "unable to hit their target",
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


def build_detailed_final_opinion(
    sentiment: Dict[str, Any],
    positive_points: List[str],
    negative_points: List[str],
    summary_text: str,
    rating=None,
) -> str:
    sentiment_label = sentiment.get("label", "Mixed")
    rating_value = parse_rating_value(rating)

    rating_context = ""

    if rating_value is not None:
        if rating_value >= 8:
            rating_context = (
                f" The numeric review rating is {rating_value:.1f}/10, which is clearly strong and supports a positive overall impression."
            )
        elif rating_value >= 7:
            rating_context = (
                f" The numeric review rating is {rating_value:.1f}/10, which is still fairly positive. "
                "This means that even if the review contains harsh, scary, violent, or disturbing wording, those words may describe the movie’s content rather than the reviewer’s dislike."
            )
        elif rating_value >= 5:
            rating_context = (
                f" The numeric review rating is {rating_value:.1f}/10, which suggests a mixed or average opinion rather than a very strong reaction."
            )
        else:
            rating_context = (
                f" The numeric review rating is {rating_value:.1f}/10, which supports a negative overall impression."
            )

    if sentiment_label == "Positive":
        return (
            "The reviewer’s overall opinion is positive. "
            "They may mention intense, uncomfortable, or critical details, but those comments do not necessarily mean they disliked the movie. "
            "Instead, the review suggests that the movie was effective, memorable, or enjoyable enough to leave a good impression. "
            "Overall, the reviewer would likely recommend the movie, especially to viewers who are interested in this genre or style."
            + rating_context
        )

    if sentiment_label == "Negative":
        return (
            "The reviewer’s overall opinion is negative. "
            "Although there may be a few small positive remarks, the stronger message of the review is disappointment or dissatisfaction. "
            "The criticism seems to focus on important parts of the movie, such as story quality, pacing, execution, or overall enjoyment. "
            "Because of that, the reviewer does not strongly recommend the movie."
            + rating_context
        )

    return (
        "The reviewer’s overall opinion is mixed. "
        "The review contains both appreciation and criticism, so the final impression is not fully positive or fully negative. "
        "Some elements of the movie appear to work well, while other parts reduce the reviewer’s enjoyment. "
        "This means the movie may still be worth watching for some viewers, but it is not being praised without reservation."
        + rating_context
    )


def generate_review_insights(
    text: str,
    summary_sents: List[str],
    sentiment: Dict[str, Any],
    rating=None,
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

    sentiment_label = sentiment.get("label", "Mixed")

    if sentiment_label == "Negative" and not negative_points:
        negative_points = summary_sents[:2] or [
            "The review expresses a negative overall opinion but does not contain a clearly isolated negative sentence."
        ]

    if sentiment_label == "Positive" and not positive_points:
        positive_points = summary_sents[:2] or [
            "The review expresses a positive overall opinion but does not contain a clearly isolated positive sentence."
        ]

    if sentiment_label == "Mixed":
        if not positive_points:
            positive_points = ["The review contains some favorable or appreciative observations."]
        if not negative_points:
            negative_points = ["The review also contains criticism or reservations about the movie."]

    if not positive_points:
        positive_points = ["The review does not clearly mention specific positive points."]

    if not negative_points:
        negative_points = ["The review does not clearly mention major negative points."]

    if not summary_text:
        summary_text = "No clear summary could be generated from this review."

    final_opinion = build_detailed_final_opinion(
        sentiment=sentiment,
        positive_points=positive_points,
        negative_points=negative_points,
        summary_text=summary_text,
        rating=rating,
    )

    return {
        "overall_summary": summary_text,
        "positive_points": positive_points,
        "negative_points": negative_points,
        "final_opinion": final_opinion,
    }


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
    vader_compound = float(sentiment.get("vader_compound", 0))
    final_compound = float(sentiment.get("compound", 0))

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

    if vader_compound > 0.5 and final_compound < -0.2:
        confidence -= 15

    if vader_compound < -0.5 and final_compound > 0.2:
        confidence -= 15

    if positive_hits > 0 and negative_hits > 0:
        confidence -= 8

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
    rating=None,
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

    ents_summary = ner_entities(summary_text) if summary_text else []
    ents_summary = ents_summary[:15]

    sentiment = analyze_sentiment(text, rating=rating)

    insights = generate_review_insights(
        text=text,
        summary_sents=summary_sents,
        sentiment=sentiment,
        rating=rating,
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