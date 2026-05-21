const movieGrid = document.getElementById("movieGrid");
const movieSearch = document.getElementById("movieSearch");
const movieCount = document.getElementById("movieCount");

let MOVIES = [];

function esc(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderMovieGrid(filterText = "") {
  const q = (filterText || "").trim().toLowerCase();
  const filtered = q
    ? MOVIES.filter(m => (m.title || "").toLowerCase().includes(q))
    : MOVIES;

  if (movieCount) movieCount.textContent = `${filtered.length} movies`;

  movieGrid.innerHTML = filtered.map(m => {
    const meta = `${m.year ? esc(m.year) : ""}${m.genre ? (m.year ? " • " : "") + esc(m.genre) : ""}`;

    return `
      <div class="poster" data-movieid="${esc(m.movie_id)}" tabindex="0" role="button">
        <img src="${esc(m.poster_url)}" alt="${esc(m.title)} poster" loading="lazy"/>
        <div class="poster-meta">
          <div class="poster-title">${esc(m.title)}</div>
          <div class="poster-year">${meta}</div>
        </div>
      </div>
    `;
  }).join("");

  for (const el of document.querySelectorAll(".poster[data-movieid]")) {
    const open = () => {
      const id = el.getAttribute("data-movieid");
      if (!id) return;
      window.location.href = `/movie/${encodeURIComponent(id)}`;
    };

    el.addEventListener("click", open);
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") open();
    });
  }
}

async function loadMovies() {
  const res = await fetch("/api/movies");
  const data = await res.json();

  if (!data.ok) {
    movieGrid.innerHTML = `<div class="muted">Failed to load movies</div>`;
    return;
  }

  MOVIES = data.movies || [];
  renderMovieGrid(movieSearch?.value || "");
}

movieSearch?.addEventListener("input", () => renderMovieGrid(movieSearch.value));

(async function init() {
  await loadMovies();
})();
