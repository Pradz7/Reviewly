from flask import Flask, jsonify, render_template, request
from pipeline import (
    list_movies_rich,
    get_reviews_for_movie_id,
    get_row_by_id,
    analyze_review,
    TEXT_COL,
)

app = Flask(__name__)

def safe_str(x):
    return "" if x is None else str(x)

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/movie/<movie_id>")
def movie_page(movie_id: str):
    # Find movie metadata for header (title/year/poster)
    movies = list_movies_rich(limit=2000)
    movie = next((m for m in movies if str(m.get("movie_id")) == str(movie_id)), None)

    # Fallback if not found
    if movie is None:
        movie = {"movie_id": movie_id, "title": movie_id, "year": "", "poster_url": ""}

    return render_template("movie.html", movie=movie)

@app.get("/api/movies")
def api_movies():
    return jsonify({"ok": True, "movies": list_movies_rich(limit=250)})

@app.get("/api/reviews")
def api_reviews():
    movie_id = request.args.get("movie_id", "").strip()
    if not movie_id:
        return jsonify({"ok": False, "error": "movie_id is required"}), 400

    sub = get_reviews_for_movie_id(movie_id, limit=200)  # raise limit for "all reviews" page
    if sub.empty:
        return jsonify({"ok": True, "reviews": []})

    rating_col = "review_rating" if "review_rating" in sub.columns else ("rating" if "rating" in sub.columns else None)
    title_col = "review_title" if "review_title" in sub.columns else None

    reviews = []
    for _, r in sub.iterrows():
        text = str(r.get(TEXT_COL, "") or "")
        preview = text[:220] + ("..." if len(text) > 220 else "")
        reviews.append({
            "row_id": int(r["_row_id"]),
            "review_title": str(r.get(title_col) or "") if title_col else "",
            "rating": str(r.get(rating_col) or "") if rating_col else "",
            "preview": preview,
        })

    return jsonify({"ok": True, "reviews": reviews})

@app.get("/api/review")
def api_review_detail():
    row_id = request.args.get("row_id", "").strip()
    if not row_id.isdigit():
        return jsonify({"ok": False, "error": "row_id must be an integer"}), 400

    row = get_row_by_id(int(row_id))

    original_text = safe_str(row.get("review_clean", row.get("review", "")))
    rating = safe_str(row.get("review_rating", row.get("rating", "")))
    review_title = safe_str(row.get("review_title", ""))

    analysis = analyze_review(original_text)

    return jsonify({
        "ok": True,
        "row_id": int(row_id),
        "review_title": review_title,
        "rating": rating,
        "original_text": original_text,
        "summary_sentences": analysis["summary_sentences"],
        "summary_text": analysis["summary_text"],
        "entities_summary": analysis["entities_summary"],
    })

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
