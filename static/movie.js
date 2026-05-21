const reviewsListPage = document.getElementById("reviewsListPage");
const reviewsEmptyPage = document.getElementById("reviewsEmptyPage");
const reviewsCount = document.getElementById("reviewsCount");

const modalOverlay = document.getElementById("modalOverlay");
const modalClose = document.getElementById("modalClose");
const detailMovie = document.getElementById("detailMovie");
const detailRatingBadge = document.getElementById("detailRatingBadge");
const detailRowIdBadge = document.getElementById("detailRowIdBadge");
const detailTitleRow = document.getElementById("detailTitleRow");
const detailTitle = document.getElementById("detailTitle");
const detailOriginal = document.getElementById("detailOriginal");
const detailSummaryList = document.getElementById("detailSummaryList");
const detailHighlighted = document.getElementById("detailHighlighted");
const detailLegend = document.getElementById("detailLegend");

const MOVIE = window.__MOVIE__ || { movie_id: "", title: "" };

function esc(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function openModal() {
  modalOverlay.classList.remove("hidden");
  modalOverlay.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";
}
function closeModal() {
  modalOverlay.classList.add("hidden");
  modalOverlay.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
}
modalClose.addEventListener("click", closeModal);
modalOverlay.addEventListener("click", (e) => { if (e.target === modalOverlay) closeModal(); });
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !modalOverlay.classList.contains("hidden")) closeModal();
});

function renderHighlighted(text, ents) {
  const sorted = [...ents].sort((a,b) => a.start - b.start);
  let out = "";
  let cur = 0;

  for (const e of sorted) {
    const s = Math.max(0, Math.min(text.length, e.start));
    const t = Math.max(0, Math.min(text.length, e.end));
    if (s < cur) continue;

    out += esc(text.slice(cur, s));
    out += `<mark class="ent" data-label="${esc(e.label)}">${esc(text.slice(s, t))}</mark>`;
    cur = t;
  }
  out += esc(text.slice(cur));
  return out;
}

async function loadReviews() {
  const res = await fetch(`/api/reviews?movie_id=${encodeURIComponent(MOVIE.movie_id)}`);
  const data = await res.json();

  if (!data.ok) {
    reviewsListPage.innerHTML = `<div class="muted">Failed: ${esc(data.error || "")}</div>`;
    return;
  }

  const reviews = data.reviews || [];
  reviewsCount.textContent = `${reviews.length} reviews loaded`;

  if (reviews.length === 0) {
    reviewsEmptyPage.classList.remove("hidden");
    reviewsListPage.innerHTML = "";
    return;
  }

  reviewsEmptyPage.classList.add("hidden");

  reviewsListPage.innerHTML = reviews.map(r => {
    const rating = r.rating ? `⭐ ${esc(r.rating)}` : "⭐ N/A";
    const titleLine = r.review_title ? `<div class="reviewTitle">${esc(r.review_title)}</div>` : "";
    return `
      <div class="reviewRow" data-rowid="${r.row_id}" role="button" tabindex="0">
        <div class="reviewRowTop">
          <span class="badge">${rating}</span>
          <span class="badge subtle">ID ${esc(r.row_id)}</span>
        </div>
        ${titleLine}
        <div class="preview">${esc(r.preview)}</div>
      </div>
    `;
  }).join("");

  for (const row of document.querySelectorAll(".reviewRow[data-rowid]")) {
    const open = async () => {
      await loadReviewDetail(row.getAttribute("data-rowid"));
    };
    row.addEventListener("click", open);
    row.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") open();
    });
  }
}

async function loadReviewDetail(rowId) {
  openModal();

  detailMovie.textContent = MOVIE.title || "";
  detailRatingBadge.textContent = "⭐ …";
  detailRowIdBadge.textContent = `ID ${rowId}`;
  detailTitleRow.classList.add("hidden");
  detailTitle.textContent = "";
  detailOriginal.textContent = "Loading...";
  detailSummaryList.innerHTML = `<li class="muted">Loading…</li>`;
  detailHighlighted.innerHTML = `<span class="muted">Loading…</span>`;
  detailLegend.innerHTML = "";

  const res = await fetch(`/api/review?row_id=${encodeURIComponent(rowId)}`);
  const data = await res.json();

  if (!data.ok) {
    detailOriginal.textContent = "";
    detailHighlighted.innerHTML = `<span class="muted">Failed: ${esc(data.error || "")}</span>`;
    return;
  }

  detailRatingBadge.textContent = `⭐ ${data.rating || "N/A"}`;

  if (data.review_title && data.review_title.trim()) {
    detailTitleRow.classList.remove("hidden");
    detailTitle.textContent = data.review_title;
  } else {
    detailTitleRow.classList.add("hidden");
  }

  detailOriginal.textContent = data.original_text || "";

  const sents = data.summary_sentences || [];
  detailSummaryList.innerHTML = sents.length
    ? sents.map(s => `<li>${esc(s)}</li>`).join("")
    : `<li class="muted">No summary produced.</li>`;

  const summaryText = data.summary_text || "";
  const ents = data.entities_summary || [];
  detailHighlighted.innerHTML = summaryText
    ? renderHighlighted(summaryText, ents)
    : `<span class="muted">No summary text.</span>`;

  const labels = [...new Set(ents.map(e => e.label))];
  detailLegend.innerHTML = labels.length
    ? labels.map(l => `<span class="chip">${esc(l)}</span>`).join("")
    : `<span class="muted">No entities found.</span>`;
}

loadReviews();
