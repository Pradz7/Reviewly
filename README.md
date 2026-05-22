# Reviewly

Reviewly is a web-based movie review analysis application that helps users understand movie reviews faster using Natural Language Processing. The system allows users to browse movies, open a movie detail page, read user reviews, generate summaries, analyze sentiment, extract keywords, and detect important entities from review text.

## Project Overview

Movie reviews are often long and contain many opinions, names, movie-related terms, and emotional expressions. Reading every review manually can take time, especially when users only want to understand the main opinion quickly.

Reviewly solves this problem by providing an AI-powered review analysis interface. Users can select a movie, open its reviews, and view an automatic analysis that includes the original review, summary, sentiment result, keywords, AI confidence score, review insights, and AI-labeled summary.

The project is built using Flask for the backend, HTML, CSS, and JavaScript for the frontend, and NLP libraries such as spaCy, TF-IDF, and VADER Sentiment Analysis for text processing.

## Main Features

- Movie browsing
- Movie detail page
- Review list
- Review summarization
- Sentiment analysis
- AI review insights
- Keyword extraction
- AI confidence score
- AI-labeled summary
- Named Entity Recognition
- Review aspect detection

## AI Analysis Features

For each selected review, Reviewly can display:

- Original review
- Generated summary
- Sentiment result
- Positive, neutral, and negative percentage
- AI confidence score
- Important keywords
- Positive points
- Negative points
- Final opinion
- AI-labeled summary

The AI-labeled summary can detect labels such as:

- PERSON
- ACTOR
- CHARACTER
- MOVIE_TITLE
- ORGANIZATION
- LOCATION
- ASPECT

## Tech Stack

### Backend

- Python
- Flask
- Pandas
- NumPy
- spaCy
- scikit-learn
- VADER Sentiment Analysis
- KaggleHub

### Frontend

- HTML
- CSS
- JavaScript
- Tailwind CSS

### Dataset

This project uses the Kaggle dataset:

```text
shivvm/popular-movies-imdb-reviews-dataset
```

The dataset contains movie information and IMDb review data.

## Project Structure

```text
Reviewly/
│
├── app.py
├── pipeline.py
├── requirements.txt
├── posters.csv
├── README.md
│
├── templates/
│   ├── index.html
│   └── movie.html
│
├── static/
│   ├── app.js
│   ├── movie.js
│   ├── styles.css
│   └── posters/
│
└── venv/
```

## How to Run the Project

### 1. Clone the Repository

```bash
git clone https://github.com/Pradz7/Reviewly.git
cd Reviewly
```

### 2. Create a Virtual Environment

For macOS or Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

For Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install spaCy English Model

```bash
python -m spacy download en_core_web_sm
```

### 5. Run the Flask App

```bash
python app.py
```

The terminal should show:

```bash
Running on http://127.0.0.1:5000
```

### 6. Open the Website

Open this URL in your browser:

```text
http://127.0.0.1:5000/
```

## How the System Works

### 1. Dataset Loading

The dataset is loaded using KaggleHub. If the online dataset cannot be loaded, the project can also use local CSV files placed inside a `data` folder.

### 2. Movie Listing

The app reads movie data and displays it on the dashboard page. Users can search and open a movie page.

### 3. Review Selection

When a review is selected, the frontend sends a request to the Flask API using the review row ID.

### 4. NLP Processing

The review text is processed by `pipeline.py`. The system performs:

- Text cleaning
- Sentence splitting
- Extractive summarization
- Sentiment analysis
- Keyword extraction
- Named Entity Recognition
- Review aspect detection
- AI confidence scoring
- Review insight generation

### 5. Display Result

The processed result is returned as JSON and displayed in the modal on the movie detail page.

## API Endpoints

### Get Movies

```http
GET /api/movies
```

Returns a list of movies.

### Get Reviews by Movie ID

```http
GET /api/reviews?movie_id=<movie_id>
```

Returns reviews for a selected movie.

### Get Review Analysis

```http
GET /api/review?row_id=<row_id>
```

Returns detailed AI analysis for one review.

## Example Output

For each selected review, the system displays:

- Original Review
- Summary
- Sentiment Analysis
- AI Confidence
- Keywords
- AI Review Insights
- AI-labeled Summary

## Common Issue

If the website does not update after editing HTML, CSS, or JavaScript files, restart Flask and hard refresh the browser.

Restart Flask:

```bash
Control + C
python app.py
```

Hard refresh on macOS:

```text
Command + Shift + R
```

Hard refresh on Windows:

```text
Ctrl + Shift + R
```

## License

This project is created for learning and academic purposes.