import os
import time
import pandas as pd
import requests

API_KEY = os.getenv("OMDB_API_KEY", "").strip()

OUTPUT_FILE = "posters.csv"
LOCAL_MOVIES_FILE = "data/imdb_list.csv"


def safe_str(value):
    if value is None:
        return ""

    text = str(value).strip()

    if text.lower() == "nan":
        return ""

    return text


def is_valid_poster_url(value):
    value = safe_str(value)

    if not value:
        return False

    if value == "N/A":
        return False

    return value.startswith("http://") or value.startswith("https://")


def load_movies():
    if os.path.exists(LOCAL_MOVIES_FILE):
        print(f"Loading movies from {LOCAL_MOVIES_FILE}")
        movies = pd.read_csv(LOCAL_MOVIES_FILE)

        id_col = "id" if "id" in movies.columns else ("imdb_id" if "imdb_id" in movies.columns else None)
        title_col = "title" if "title" in movies.columns else None

        if id_col is None:
            raise RuntimeError("Could not find IMDb ID column. Expected 'id' or 'imdb_id'.")

        if title_col is None:
            movies["title"] = ""
            title_col = "title"

        movies = movies[[id_col, title_col]].dropna(subset=[id_col]).copy()
        movies = movies.rename(columns={id_col: "movie_id", title_col: "title"})
        movies["movie_id"] = movies["movie_id"].astype(str).str.strip()
        movies["title"] = movies["title"].astype(str).str.strip()
        movies = movies.drop_duplicates(subset=["movie_id"])

        return movies

    print("Local data/imdb_list.csv not found. Trying to load movies from pipeline.py...")

    from pipeline import df_all

    if "imdb_id" in df_all.columns:
        id_col = "imdb_id"
    elif "id" in df_all.columns:
        id_col = "id"
    else:
        raise RuntimeError("Could not find IMDb ID column in pipeline.df_all.")

    title_col = "title" if "title" in df_all.columns else None

    if title_col:
        movies = df_all[[id_col, title_col]].dropna(subset=[id_col]).copy()
        movies = movies.rename(columns={id_col: "movie_id", title_col: "title"})
    else:
        movies = df_all[[id_col]].dropna(subset=[id_col]).copy()
        movies = movies.rename(columns={id_col: "movie_id"})
        movies["title"] = ""

    movies["movie_id"] = movies["movie_id"].astype(str).str.strip()
    movies["title"] = movies["title"].astype(str).str.strip()
    movies = movies.drop_duplicates(subset=["movie_id"])

    return movies


def load_existing_posters():
    if not os.path.exists(OUTPUT_FILE):
        return pd.DataFrame(columns=["movie_id", "title", "poster_url", "poster_file"])

    existing = pd.read_csv(OUTPUT_FILE)

    if "movie_id" not in existing.columns:
        return pd.DataFrame(columns=["movie_id", "title", "poster_url", "poster_file"])

    if "title" not in existing.columns:
        existing["title"] = ""

    if "poster_url" not in existing.columns:
        existing["poster_url"] = ""

    if "poster_file" not in existing.columns:
        existing["poster_file"] = ""

    existing["movie_id"] = existing["movie_id"].astype(str).str.strip()
    existing["title"] = existing["title"].astype(str).str.strip()
    existing["poster_url"] = existing["poster_url"].astype(str).str.strip()
    existing["poster_file"] = existing["poster_file"].astype(str).str.strip()

    existing = existing.drop_duplicates(subset=["movie_id"], keep="last")

    return existing[["movie_id", "title", "poster_url", "poster_file"]]


def test_api_key():
    if not API_KEY:
        raise RuntimeError(
            "OMDB_API_KEY is empty. Run this first:\n"
            'export OMDB_API_KEY="YOUR_KEY_HERE"'
        )

    test_id = "tt3896198"
    url = "https://www.omdbapi.com/"

    params = {
        "i": test_id,
        "apikey": API_KEY
    }

    response = requests.get(url, params=params, timeout=15)
    data = response.json()

    if data.get("Response") == "False":
        raise RuntimeError(f"OMDb API key test failed: {data.get('Error', 'Unknown error')}")

    print("OMDb API key works.")


def fetch_poster_from_omdb(imdb_id):
    url = "https://www.omdbapi.com/"

    params = {
        "i": imdb_id,
        "apikey": API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
    except Exception as e:
        print(f"Request failed for {imdb_id}: {e}")
        return ""

    if data.get("Response") == "False":
        print(f"OMDb error for {imdb_id}: {data.get('Error', 'Unknown error')}")
        return ""

    poster_url = safe_str(data.get("Poster"))

    if not is_valid_poster_url(poster_url):
        return ""

    return poster_url


def main():
    test_api_key()

    movies = load_movies()
    existing = load_existing_posters()

    existing_by_id = {
        safe_str(row["movie_id"]): row
        for _, row in existing.iterrows()
        if safe_str(row["movie_id"])
    }

    print(f"Total movies found: {len(movies)}")
    print(f"Existing poster rows: {len(existing_by_id)}")

    new_count = 0
    updated_count = 0
    skipped_count = 0
    missing_count = 0

    for _, movie in movies.iterrows():
        movie_id = safe_str(movie.get("movie_id"))
        title = safe_str(movie.get("title"))

        if not movie_id:
            continue

        existing_row = existing_by_id.get(movie_id)

        if existing_row is not None:
            existing_url = safe_str(existing_row.get("poster_url"))

            if is_valid_poster_url(existing_url):
                print(f"Skipping existing URL: {title} ({movie_id})")
                skipped_count += 1
                continue

        print(f"Fetching poster: {title} ({movie_id})")

        poster_url = fetch_poster_from_omdb(movie_id)

        if poster_url:
            old_poster_file = ""

            if existing_row is not None:
                old_poster_file = safe_str(existing_row.get("poster_file"))

            existing_by_id[movie_id] = {
                "movie_id": movie_id,
                "title": title,
                "poster_url": poster_url,
                "poster_file": old_poster_file
            }

            if existing_row is None:
                new_count += 1
                print(f"Saved new: {title}")
            else:
                updated_count += 1
                print(f"Updated with URL: {title}")

        else:
            missing_count += 1
            print(f"No poster found: {title}")

        rows = list(existing_by_id.values())
        pd.DataFrame(rows).to_csv(OUTPUT_FILE, index=False)

        time.sleep(0.25)

    rows = list(existing_by_id.values())
    pd.DataFrame(rows).to_csv(OUTPUT_FILE, index=False)

    print("")
    print("Done.")
    print(f"New poster rows: {new_count}")
    print(f"Updated poster URLs: {updated_count}")
    print(f"Skipped valid URLs: {skipped_count}")
    print(f"Missing posters: {missing_count}")
    print(f"Output file: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()