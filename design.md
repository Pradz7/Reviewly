# Reviewly Design System

## 1. Visual Theme & Atmosphere

Reviewly uses a dark cinematic visual style designed for a movie review summarization and Named Entity Recognition website. The interface should feel modern, clean, and movie-focused, but it should not copy IMDb directly. Instead, Reviewly has its own identity by combining a deep dark background, warm amber highlights, soft red movie accents, and blue AI-inspired elements.

The overall mood is intelligent, cinematic, and simple. Users should feel like they are using an AI-powered movie review dashboard where long reviews can be turned into short summaries and important named entities can be extracted clearly.

**Key Characteristics**

- Dark cinematic background for a premium movie-review feeling
- Warm amber accent for main actions and highlights
- Soft red accent for movie-related labels and important details
- Blue accent for AI, summarization, and NER results
- Clean cards with rounded corners
- Readable typography with strong contrast
- Poster-focused movie browsing experience
- Clear separation between original review, summary, and NER results
- Responsive layout for desktop, tablet, and mobile

---

## 2. Color Palette & Roles

The Reviewly color palette is movie-inspired but not the same as IMDb. It keeps the cinematic dark feeling while using a different accent system.

### Primary Colors

- **Midnight Black** (`#0D0D12`)  
  Main page background. Used for the body, hero background, and main layout.

- **Dark Graphite** (`#17171F`)  
  Secondary section background. Used for large page sections.

- **Charcoal Panel** (`#20202A`)  
  Main card background. Used for movie cards, review cards, and analysis cards.

- **Soft Dark Panel** (`#292934`)  
  Elevated card background. Used for highlighted cards or focused content.

### Accent Colors

- **Warm Amber** (`#FFB703`)  
  Primary accent color. Used for main buttons, active states, selected items, ratings, and important highlights.

- **Cinema Red** (`#E63946`)  
  Secondary movie accent. Used for movie-related labels, warnings, and important emphasis.

- **AI Blue** (`#4CC9F0`)  
  AI-related accent. Used for summary cards, NER sections, and analysis labels.

- **Fresh Teal** (`#2DD4BF`)  
  Success or positive accent. Used for successful analysis states or completed actions.

### Text Colors

- **Soft White** (`#F8FAFC`)  
  Main text on dark backgrounds.

- **Cool Gray** (`#CBD5E1`)  
  Secondary text, descriptions, and paragraph content.

- **Slate Gray** (`#94A3B8`)  
  Muted text, metadata, captions, and helper text.

### Border and State Colors

- **Soft Border** (`#343442`)  
  Main border color for cards, inputs, and dividers.

- **Deep Input** (`#111118`)  
  Input field background.

- **Soft Red** (`#F87171`)  
  Error messages and failed states.

---

## 3. CSS Variables

Use these CSS variables in `static/css/style.css`.

```css
:root {
  --color-bg-main: #0D0D12;
  --color-bg-secondary: #17171F;
  --color-bg-card: #20202A;
  --color-bg-elevated: #292934;
  --color-bg-input: #111118;

  --color-primary: #FFB703;
  --color-secondary: #E63946;
  --color-ai: #4CC9F0;
  --color-success: #2DD4BF;
  --color-error: #F87171;

  --color-text-primary: #F8FAFC;
  --color-text-secondary: #CBD5E1;
  --color-text-muted: #94A3B8;

  --color-border: #343442;
  --color-white: #FFFFFF;
  --color-black: #000000;

  --radius-sm: 8px;
  --radius-md: 14px;
  --radius-lg: 20px;
  --radius-full: 999px;

  --shadow-card: 0 18px 40px rgba(0, 0, 0, 0.35);
  --shadow-hover: 0 24px 60px rgba(0, 0, 0, 0.45);
}
```

---

## 4. Typography Rules

### Font Family

Reviewly should use a clean modern sans-serif font.

```css
body {
  font-family: "Inter", "Poppins", Arial, sans-serif;
}
```

Alternative font:

```css
body {
  font-family: "Roboto", Arial, sans-serif;
}
```

### Typography Hierarchy

| Role | Size | Weight | Line Height | Usage |
|---|---:|---:|---:|---|
| Hero Title | 56px | 800 | 1.05 | Main hero heading |
| Page Title | 42px | 800 | 1.15 | Movie detail title |
| Section Title | 32px | 700 | 1.25 | Browse Movies, Reviews |
| Card Title | 20px | 700 | 1.4 | Movie title, review title |
| Body Large | 18px | 400 | 1.7 | Hero subtitle |
| Body Regular | 16px | 400 | 1.7 | Review text, descriptions |
| Body Small | 14px | 400 | 1.5 | Metadata, helper text |
| Badge Text | 12px | 700 | 1.2 | Labels and entity types |
| Button Text | 14px | 700 | 1.2 | Buttons |

### Typography Principles

- Use strong contrast between text and background.
- Use bold titles for movie names and section headings.
- Use readable body text for reviews and summaries.
- Do not make paragraphs too narrow or too wide.
- Use muted text only for metadata, not for important content.

---

## 5. Base Layout

The website should use a dark full-page layout.

```css
* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  background: var(--color-bg-main);
  color: var(--color-text-primary);
  font-family: "Inter", "Poppins", Arial, sans-serif;
}

a {
  color: inherit;
}

p {
  color: var(--color-text-secondary);
}

img {
  max-width: 100%;
}
```

---

## 6. Navigation Bar

The navbar should be fixed or sticky at the top. It should feel simple, dark, and modern.

### Navbar Content

Left side:

```text
Reviewly
```

Right side:

```text
Home | Movies | About | GitHub
```

### Navbar Styling

```css
.navbar {
  background: rgba(13, 13, 18, 0.88);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--color-border);
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 48px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.logo {
  font-size: 24px;
  font-weight: 800;
  color: var(--color-text-primary);
  letter-spacing: -0.5px;
}

.logo span {
  color: var(--color-primary);
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 28px;
}

.nav-links a {
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: 0.2s ease;
}

.nav-links a:hover {
  color: var(--color-primary);
}
```

---

## 7. Hero Section

The hero section should introduce the project clearly.

### Hero Copy

```text
Reviewly

Understand movie reviews faster with AI.

Reviewly summarizes long movie reviews and extracts important named entities such as people, places, organizations, movie titles, and dates.
```

### Hero Layout

Desktop:

```text
Left: Title, subtitle, buttons
Right: Preview analysis card
```

Mobile:

```text
Top: Title and subtitle
Bottom: Preview analysis card
```

### Hero CSS

```css
.hero {
  min-height: 640px;
  background:
    radial-gradient(circle at top left, rgba(255, 183, 3, 0.16), transparent 30%),
    radial-gradient(circle at bottom right, rgba(76, 201, 240, 0.12), transparent 35%),
    var(--color-bg-main);
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  align-items: center;
  gap: 56px;
  padding: 80px 72px;
}

.hero-content h1 {
  font-size: 56px;
  font-weight: 800;
  line-height: 1.05;
  margin: 0 0 20px;
  color: var(--color-text-primary);
}

.hero-content h1 span {
  color: var(--color-primary);
}

.hero-content p {
  max-width: 620px;
  font-size: 18px;
  line-height: 1.7;
  color: var(--color-text-secondary);
  margin-bottom: 32px;
}

.hero-actions {
  display: flex;
  gap: 16px;
  align-items: center;
}

.hero-preview {
  background: linear-gradient(145deg, var(--color-bg-card), var(--color-bg-elevated));
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-card);
}
```

---

## 8. Buttons

### Primary Button

Used for the main action, such as browsing movies or analyzing reviews.

```css
.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: var(--color-black);
  border: none;
  border-radius: var(--radius-full);
  padding: 12px 22px;
  font-size: 14px;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  transition: 0.2s ease;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(255, 183, 3, 0.25);
}
```

### Secondary Button

Used for secondary actions.

```css
.btn-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  padding: 12px 22px;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: 0.2s ease;
}

.btn-secondary:hover {
  border-color: var(--color-ai);
  color: var(--color-ai);
  background: rgba(76, 201, 240, 0.08);
}
```

### Danger Button

Used only for warnings or destructive actions.

```css
.btn-danger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-secondary);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-full);
  padding: 12px 22px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}
```

---

## 9. Movie Browse Section

The movie browse section should display movies in a poster-focused grid.

### Section Content

```text
Browse Movies

Select a movie to view reviews, generate a summary, and extract named entities.
```

### Movie Grid CSS

```css
.movies-section {
  padding: 72px;
  background: var(--color-bg-secondary);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 24px;
  margin-bottom: 32px;
}

.section-header h2 {
  font-size: 32px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
}

.section-header p {
  color: var(--color-text-muted);
  margin-top: 8px;
}

.movie-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 28px;
}
```

---

## 10. Movie Card

Each movie card should display:

- Movie poster
- Movie title
- Year or metadata
- Analyze link

```css
.movie-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-card);
  transition: 0.25s ease;
}

.movie-card:hover {
  transform: translateY(-8px);
  box-shadow: var(--shadow-hover);
  border-color: rgba(255, 183, 3, 0.45);
}

.movie-poster {
  width: 100%;
  aspect-ratio: 2 / 3;
  object-fit: cover;
  display: block;
}

.movie-info {
  padding: 18px;
}

.movie-info h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 8px;
}

.movie-meta {
  font-size: 13px;
  color: var(--color-text-muted);
  margin-bottom: 14px;
}

.movie-card a {
  color: var(--color-primary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 700;
}

.movie-card a:hover {
  color: var(--color-ai);
}
```

---

## 11. Search Bar

The search bar helps users quickly find a movie.

```css
.search-wrapper {
  max-width: 520px;
  width: 100%;
  position: relative;
}

.search-input {
  width: 100%;
  background: var(--color-bg-input);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  padding: 14px 18px;
  font-size: 14px;
  outline: none;
  transition: 0.2s ease;
}

.search-input::placeholder {
  color: var(--color-text-muted);
}

.search-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px rgba(255, 183, 3, 0.12);
}
```

---

## 12. Movie Detail Page

The movie detail page should focus on the selected movie.

### Detail Page Content

- Movie poster
- Movie title
- Movie metadata
- Short instruction text
- Review list
- Analysis result

### Movie Detail CSS

```css
.movie-detail {
  padding: 72px;
  background: var(--color-bg-main);
}

.movie-detail-header {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 40px;
  align-items: center;
  background: linear-gradient(145deg, var(--color-bg-secondary), var(--color-bg-card));
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 32px;
  box-shadow: var(--shadow-card);
}

.detail-poster {
  width: 100%;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

.detail-content h1 {
  font-size: 42px;
  font-weight: 800;
  color: var(--color-text-primary);
  margin: 0 0 12px;
}

.detail-meta {
  color: var(--color-primary);
  font-weight: 600;
  margin-bottom: 18px;
}

.detail-description {
  color: var(--color-text-secondary);
  line-height: 1.7;
  max-width: 720px;
}
```

---

## 13. Review List

Each review should appear as a readable card.

```css
.review-section {
  margin-top: 56px;
}

.review-section h2 {
  font-size: 28px;
  color: var(--color-text-primary);
  margin-bottom: 24px;
}

.review-list {
  display: grid;
  gap: 20px;
}

.review-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 24px;
  transition: 0.2s ease;
}

.review-card:hover {
  border-color: rgba(76, 201, 240, 0.45);
  transform: translateY(-3px);
}

.review-card h3 {
  font-size: 20px;
  color: var(--color-text-primary);
  margin: 0 0 10px;
}

.review-card p {
  color: var(--color-text-secondary);
  line-height: 1.7;
}

.review-rating {
  display: inline-flex;
  align-items: center;
  background: rgba(255, 183, 3, 0.12);
  color: var(--color-primary);
  border: 1px solid rgba(255, 183, 3, 0.35);
  border-radius: var(--radius-full);
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 14px;
}
```

---

## 14. Analysis Result Section

The analysis result should be separated into three cards:

1. Original Review
2. AI Summary
3. Named Entities

```css
.analysis-section {
  margin-top: 56px;
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
}

.analysis-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 28px;
  box-shadow: var(--shadow-card);
}

.analysis-card h3 {
  font-size: 22px;
  color: var(--color-text-primary);
  margin: 0 0 16px;
}

.analysis-card p {
  color: var(--color-text-secondary);
  line-height: 1.8;
}

.summary-card {
  border-color: rgba(76, 201, 240, 0.45);
  background:
    linear-gradient(145deg, rgba(76, 201, 240, 0.08), transparent),
    var(--color-bg-card);
}

.summary-label {
  display: inline-block;
  background: rgba(76, 201, 240, 0.12);
  color: var(--color-ai);
  border: 1px solid rgba(76, 201, 240, 0.35);
  border-radius: var(--radius-full);
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 14px;
}
```

---

## 15. NER Entity Chips

NER results should be displayed as chips so users can easily scan the extracted entities.

```css
.entity-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
}

.entity-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 183, 3, 0.1);
  color: var(--color-text-primary);
  border: 1px solid rgba(255, 183, 3, 0.35);
  border-radius: var(--radius-full);
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 600;
}

.entity-type {
  color: var(--color-primary);
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
}
```

### Entity Type Color Variants

```css
.entity-person {
  background: rgba(255, 183, 3, 0.1);
  border-color: rgba(255, 183, 3, 0.35);
}

.entity-org {
  background: rgba(76, 201, 240, 0.1);
  border-color: rgba(76, 201, 240, 0.35);
}

.entity-location {
  background: rgba(45, 212, 191, 0.1);
  border-color: rgba(45, 212, 191, 0.35);
}

.entity-work {
  background: rgba(230, 57, 70, 0.1);
  border-color: rgba(230, 57, 70, 0.35);
}

.entity-date {
  background: rgba(148, 163, 184, 0.12);
  border-color: rgba(148, 163, 184, 0.35);
}
```

---

## 16. Loading State

When the system is generating a summary or extracting entities, show a loading state.

```css
.loading-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 28px;
  text-align: center;
}

.loading-spinner {
  width: 42px;
  height: 42px;
  border: 4px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-card p {
  color: var(--color-text-secondary);
}
```

Loading text:

```text
Analyzing review...
Generating summary and extracting named entities.
```

---

## 17. Empty State

If there are no movies, reviews, summaries, or entities, show a friendly empty state.

```css
.empty-state {
  background: var(--color-bg-card);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-lg);
  padding: 40px;
  text-align: center;
}

.empty-state h3 {
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.empty-state p {
  color: var(--color-text-muted);
}
```

Example texts:

```text
No reviews found.
Try selecting another movie.
```

```text
No named entities were detected in this review.
```

---

## 18. Error State

Error messages should be clear but not too aggressive.

```css
.error-card {
  background: rgba(248, 113, 113, 0.1);
  border: 1px solid rgba(248, 113, 113, 0.35);
  color: var(--color-error);
  border-radius: var(--radius-lg);
  padding: 20px;
}

.error-card strong {
  color: var(--color-error);
}
```

Example text:

```text
Something went wrong while analyzing the review. Please try again.
```

---

## 19. Footer

The footer should be simple and clean.

```css
.footer {
  background: var(--color-bg-main);
  border-top: 1px solid var(--color-border);
  padding: 32px 72px;
  color: var(--color-text-muted);
  font-size: 14px;
  text-align: center;
}
```

Footer text:

```text
Reviewly — Movie Review Summarization and NER Website
```

---

## 20. Responsive Design

The layout should work well on desktop, tablet, and mobile.

### Desktop

- Navbar is horizontal.
- Hero section has two columns.
- Movie grid has 4 to 5 cards per row.
- Movie detail page uses poster on the left and information on the right.

### Tablet

- Hero section becomes one column if needed.
- Movie grid has 2 to 3 cards per row.
- Movie detail header becomes smaller.

### Mobile

- Navbar links can be hidden.
- Hero section becomes one column.
- Movie cards become one column.
- Movie detail poster and text stack vertically.
- Buttons become full width.

### Responsive CSS

```css
@media (max-width: 1024px) {
  .hero {
    grid-template-columns: 1fr;
    padding: 64px 32px;
  }

  .movies-section,
  .movie-detail {
    padding: 56px 32px;
  }

  .movie-detail-header {
    grid-template-columns: 220px 1fr;
  }
}

@media (max-width: 768px) {
  .navbar {
    padding: 0 24px;
  }

  .nav-links {
    display: none;
  }

  .hero-content h1 {
    font-size: 42px;
  }

  .hero-content p {
    font-size: 16px;
  }

  .movie-detail-header {
    grid-template-columns: 1fr;
  }

  .detail-poster {
    max-width: 260px;
  }

  .section-header {
    flex-direction: column;
    align-items: start;
    gap: 16px;
  }
}

@media (max-width: 480px) {
  .hero {
    padding: 48px 20px;
  }

  .movies-section,
  .movie-detail {
    padding: 40px 20px;
  }

  .hero-content h1 {
    font-size: 34px;
  }

  .hero-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .btn-primary,
  .btn-secondary {
    width: 100%;
    text-align: center;
  }

  .movie-grid {
    grid-template-columns: 1fr;
  }
}
```

---

## 21. Suggested HTML Structure

This is the recommended structure for the homepage.

```html
<nav class="navbar">
  <div class="logo">Review<span>ly</span></div>

  <div class="nav-links">
    <a href="/">Home</a>
    <a href="#movies">Movies</a>
    <a href="#about">About</a>
    <a href="https://github.com/Pradz7/Reviewly">GitHub</a>
  </div>
</nav>

<section class="hero">
  <div class="hero-content">
    <h1>Understand movie reviews faster with <span>AI</span>.</h1>
    <p>
      Reviewly summarizes long movie reviews and extracts important named entities
      such as people, places, organizations, movie titles, and dates.
    </p>

    <div class="hero-actions">
      <a href="#movies" class="btn-primary">Browse Movies</a>
      <a href="#analysis" class="btn-secondary">View Analysis</a>
    </div>
  </div>

  <div class="hero-preview">
    <div class="summary-label">AI Summary</div>
    <h3>Review Insight</h3>
    <p>
      A clean summary and entity extraction result will appear here after the user
      selects a movie review.
    </p>
  </div>
</section>

<section class="movies-section" id="movies">
  <div class="section-header">
    <div>
      <h2>Browse Movies</h2>
      <p>Select a movie to analyze its reviews.</p>
    </div>

    <div class="search-wrapper">
      <input class="search-input" type="text" placeholder="Search movies..." />
    </div>
  </div>

  <div class="movie-grid">
    <div class="movie-card">
      <img class="movie-poster" src="poster.jpg" alt="Movie poster" />

      <div class="movie-info">
        <h3>Movie Title</h3>
        <div class="movie-meta">2024 • Drama</div>
        <a href="#">Analyze Reviews →</a>
      </div>
    </div>
  </div>
</section>
```

---

## 22. Suggested File Structure

Recommended structure for the project:

```text
movie_review_site/
│
├── app.py
├── pipeline.py
├── requirements.txt
├── posters.csv
│
├── templates/
│   ├── index.html
│   └── movie.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   ├── js/
│   │   └── main.js
│   │
│   └── posters/
│
└── design.md
```

---

## 23. Implementation Priority

Build the new design in this order:

1. Add CSS variables.
2. Update navbar.
3. Update homepage hero section.
4. Update movie card grid.
5. Update movie detail page.
6. Update review cards.
7. Update summary result card.
8. Update NER entity chips.
9. Add loading and empty states.
10. Make the layout responsive.

---

## 24. Do's and Don'ts

### Do

- Use dark cinematic backgrounds.
- Use warm amber only for important actions and highlights.
- Use blue for AI-related sections like summary and NER.
- Keep movie posters large and clear.
- Make review text readable.
- Separate original review, summary, and NER results into different cards.
- Use responsive layouts for mobile.

### Don't

- Do not copy IMDb colors exactly.
- Do not overuse yellow or red.
- Do not make the UI too crowded.
- Do not use too many different fonts.
- Do not place text directly on images without contrast.
- Do not make NER results look like plain text only.
- Do not use low-contrast gray text for important information.

---

## 25. Final Design Direction

The final design direction for Reviewly is:

> A dark cinematic movie review analysis website with warm amber highlights, AI-blue result cards, clean movie posters, readable summaries, and clear NER entity chips.

The website should look professional, modern, and suitable for a student NLP project. It should feel related to movie review platforms, but still have its own unique identity.