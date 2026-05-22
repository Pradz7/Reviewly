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

const BLOCKED_ENTITY_WORDS = new Set([
  "it", "its", "they", "them", "he", "she", "him", "her", "his", "hers",
  "we", "you", "your", "i", "me", "my", "mine", "our", "ours", "their",
  "theirs", "this", "that", "these", "those", "what", "whattt", "whatttt",
  "whattttt", "huh", "yeah", "wow", "lol", "haha", "okay", "ok", "nope",
  "yes", "no", "maybe", "thing", "stuff",

  "open", "opened", "opening", "close", "closed", "closing", "start",
  "started", "starting", "enter", "entered", "entering", "leave", "left",
  "run", "runs", "running", "hide", "hiding", "ask", "asked", "asking",
  "go", "goes", "going", "went", "know", "knowing", "think", "thinking",

  "door", "garage", "building", "shelter", "trail", "car", "beast"
]);

const BLOCKED_LABELS = new Set([
  "PRODUCT",
  "CARDINAL",
  "ORDINAL",
  "QUANTITY",
  "PERCENT",
  "MONEY",
  "TIME",
  "DATE",
  "LAW",
  "LANGUAGE",
  "IGNORE"
]);

const AMBIGUOUS_MOVIE_TITLES = new Set([
  "it", "its", "us", "her", "up", "saw", "sing", "cars", "old", "fresh",
  "home", "life", "room", "split", "mother", "nope", "what", "open",
  "close", "run", "go", "big", "small", "yes", "no"
]);

function esc(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function isStretchedWord(text) {
  const clean = String(text || "").trim().toLowerCase();

  if (clean.length < 4) return false;

  if (!/^[a-zA-Z]+$/.test(clean)) return false;

  return /(.)\1{3,}/.test(clean);
}

function shouldRemoveEntity(entity) {
  const text = String(entity?.text || "").trim();
  const label = String(entity?.label || "").trim();
  const originalLabel = String(entity?.original_label || "").trim();

  const lower = text.toLowerCase();
  const normalizedLabel = label.toUpperCase();
  const normalizedOriginalLabel = originalLabel.toUpperCase();

  if (!text || text.length < 2) return true;

  if (BLOCKED_LABELS.has(normalizedLabel)) return true;

  if (BLOCKED_LABELS.has(normalizedOriginalLabel)) return true;

  if (BLOCKED_ENTITY_WORDS.has(lower)) return true;

  if (isStretchedWord(lower)) return true;

  if (/^[^\w]+$/.test(lower)) return true;

  if (["MOVIE_TITLE", "WORK_OF_ART"].includes(normalizedLabel) && AMBIGUOUS_MOVIE_TITLES.has(lower)) {
    return true;
  }

  if (["MOVIE_TITLE", "WORK_OF_ART"].includes(normalizedOriginalLabel) && AMBIGUOUS_MOVIE_TITLES.has(lower)) {
    return true;
  }

  if (["PERSON", "ACTOR", "CHARACTER"].includes(normalizedLabel)) {
    if (text === text.toLowerCase()) return true;
    if (lower.length <= 2) return true;
  }

  if (text.split(/\s+/).length === 1 && text === text.toLowerCase() && normalizedLabel !== "ASPECT") {
    return true;
  }

  return false;
}

function sanitizeEntities(entities) {
  const safe = [];
  const seen = new Set();

  for (const entity of entities || []) {
    if (shouldRemoveEntity(entity)) continue;

    const start = Number(entity.start);
    const end = Number(entity.end);

    if (!Number.isFinite(start) || !Number.isFinite(end)) continue;

    if (start < 0 || end <= start) continue;

    const label = String(entity.label || "").trim();
    const text = String(entity.text || "").trim();

    const key = `${start}-${end}-${label}-${text.toLowerCase()}`;

    if (seen.has(key)) continue;

    seen.add(key);

    safe.push({
      ...entity,
      start,
      end,
      label,
      text
    });
  }

  return safe.sort((a, b) => a.start - b.start);
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

modalOverlay.addEventListener("click", (e) => {
  if (e.target === modalOverlay) closeModal();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !modalOverlay.classList.contains("hidden")) {
    closeModal();
  }
});

/*
  IMPORTANT LAYOUT FIX:
  This function forces the AI cards container to be directly inside .modal-body,
  immediately after .review-top-grid.

  This prevents Sentiment, Confidence, Keywords, and AI Review Insights
  from staying inside the left or right column.
*/
function getDynamicAnalysisContainer() {
  let container = document.getElementById("dynamicAnalysisCards");
  const modalBody = document.querySelector(".modal-body");
  const reviewTopGrid = document.querySelector(".review-top-grid");

  if (!container) {
    container = document.createElement("div");
    container.id = "dynamicAnalysisCards";
  }

  container.className = "analysis-grid";
  container.removeAttribute("style");

  if (modalBody && reviewTopGrid) {
    if (container.parentElement !== modalBody) {
      modalBody.insertBefore(container, reviewTopGrid.nextSibling);
    } else if (container.previousElementSibling !== reviewTopGrid) {
      modalBody.insertBefore(container, reviewTopGrid.nextSibling);
    }
  }

  return container;
}

function clearDynamicAnalysisCards() {
  const container = getDynamicAnalysisContainer();
  container.innerHTML = "";
}

function cardWrapper(id, html) {
  const container = getDynamicAnalysisContainer();

  let box = document.getElementById(id);

  if (!box) {
    box = document.createElement("div");
    box.id = id;
  }

  if (box.parentElement !== container) {
    container.appendChild(box);
  }

  box.removeAttribute("style");
  box.innerHTML = html;

  return box;
}

function renderHighlighted(text, ents) {
  const safeEntities = sanitizeEntities(ents);
  const sorted = [...safeEntities].sort((a, b) => a.start - b.start);

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

function getSentimentColor(label) {
  const normalized = String(label || "").toLowerCase();

  if (normalized === "positive") {
    return {
      border: "rgba(45, 212, 191, 0.35)",
      background: "rgba(45, 212, 191, 0.10)",
      color: "#2DD4BF"
    };
  }

  if (normalized === "negative") {
    return {
      border: "rgba(248, 113, 113, 0.35)",
      background: "rgba(248, 113, 113, 0.10)",
      color: "#F87171"
    };
  }

  return {
    border: "rgba(255, 183, 3, 0.35)",
    background: "rgba(255, 183, 3, 0.10)",
    color: "#FFB703"
  };
}

function percent(value) {
  const n = Number(value || 0);
  return `${Math.round(n * 100)}%`;
}

function renderSentiment(sentiment) {
  if (!sentiment) {
    cardWrapper("detailSentimentBox", `
      <div class="panel">
        <h3 style="margin: 0 0 12px; color: #F8FAFC;">Sentiment Analysis</h3>
        <p class="muted">No sentiment result available.</p>
      </div>
    `);
    return;
  }

  const label = sentiment.label || "Mixed";
  const compound = sentiment.compound ?? 0;
  const positive = sentiment.positive ?? 0;
  const neutral = sentiment.neutral ?? 0;
  const negative = sentiment.negative ?? 0;
  const colors = getSentimentColor(label);

  cardWrapper("detailSentimentBox", `
    <div
      class="panel"
      style="
        border-color: ${colors.border};
        background: linear-gradient(145deg, ${colors.background}, transparent), #20202A;
      "
    >
      <div style="display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 14px;">
        <h3 style="margin: 0; color: #F8FAFC;">Sentiment Analysis</h3>

        <span
          style="
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 800;
            color: ${colors.color};
            border: 1px solid ${colors.border};
            background: ${colors.background};
          "
        >
          ${esc(label)}
        </span>
      </div>

      <div style="color: #CBD5E1; font-size: 14px; line-height: 1.8;">
        <div><strong style="color: #F8FAFC;">Compound Score:</strong> ${esc(compound)}</div>
        <div><strong style="color: #2DD4BF;">Positive:</strong> ${percent(positive)}</div>
        <div><strong style="color: #CBD5E1;">Neutral:</strong> ${percent(neutral)}</div>
        <div><strong style="color: #F87171;">Negative:</strong> ${percent(negative)}</div>
      </div>
    </div>
  `);
}

function renderConfidence(confidence) {
  if (!confidence) {
    cardWrapper("detailConfidenceBox", `
      <div class="panel">
        <h3 style="margin: 0 0 12px; color: #F8FAFC;">AI Confidence</h3>
        <p class="muted">No confidence score available.</p>
      </div>
    `);
    return;
  }

  const score = Number(confidence.score || 0);
  const level = confidence.level || "Unknown";
  const reason = confidence.reason || "No reason provided.";

  let color = "#FFB703";

  if (level === "High") color = "#2DD4BF";
  if (level === "Medium") color = "#FFB703";
  if (level === "Low") color = "#F87171";

  cardWrapper("detailConfidenceBox", `
    <div
      class="panel"
      style="
        border-color: ${color}66;
        background: linear-gradient(145deg, ${color}18, transparent), #20202A;
      "
    >
      <div style="display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 14px;">
        <h3 style="margin: 0; color: #F8FAFC;">AI Confidence</h3>

        <span
          style="
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 800;
            color: ${color};
            border: 1px solid ${color}66;
            background: ${color}18;
          "
        >
          ${esc(level)}
        </span>
      </div>

      <div style="margin-bottom: 10px;">
        <div style="display: flex; justify-content: space-between; color: #CBD5E1; font-size: 14px; margin-bottom: 6px;">
          <span>Confidence Score</span>
          <strong style="color: ${color};">${score}%</strong>
        </div>

        <div style="height: 10px; background: #111118; border-radius: 999px; overflow: hidden; border: 1px solid #343442;">
          <div style="width: ${score}%; height: 100%; background: ${color}; border-radius: 999px;"></div>
        </div>
      </div>

      <p style="margin: 0; color: #CBD5E1; font-size: 14px; line-height: 1.7;">
        ${esc(reason)}
      </p>
    </div>
  `);
}

function renderKeywords(keywords) {
  if (!keywords || keywords.length === 0) {
    cardWrapper("detailKeywordsBox", `
      <div class="panel">
        <h3 style="margin: 0 0 12px; color: #F8FAFC;">Keywords</h3>
        <p class="muted">No keywords detected.</p>
      </div>
    `);
    return;
  }

  cardWrapper("detailKeywordsBox", `
    <div
      class="panel"
      style="
        border-color: rgba(76, 201, 240, 0.35);
        background: linear-gradient(145deg, rgba(76, 201, 240, 0.08), transparent), #20202A;
      "
    >
      <h3 style="margin: 0 0 14px; color: #F8FAFC;">Keywords</h3>

      <div style="display: flex; flex-wrap: wrap; gap: 8px;">
        ${keywords.map((keyword) => `
          <span
            style="
              display: inline-flex;
              align-items: center;
              border-radius: 999px;
              border: 1px solid rgba(76, 201, 240, 0.35);
              background: rgba(76, 201, 240, 0.10);
              color: #4CC9F0;
              padding: 6px 10px;
              font-size: 12px;
              font-weight: 800;
            "
          >
            ${esc(keyword)}
          </span>
        `).join("")}
      </div>
    </div>
  `);
}

function renderInsights(insights) {
  if (!insights) {
    cardWrapper("detailInsightsBox", `
      <div class="panel">
        <h3 style="margin: 0 0 12px; color: #F8FAFC;">AI Review Insights</h3>
        <p class="muted">No insight result available.</p>
      </div>
    `);
    return;
  }

  const positivePoints = insights.positive_points || [];
  const negativePoints = insights.negative_points || [];

  cardWrapper("detailInsightsBox", `
    <div
      class="panel"
      style="
        border-color: rgba(255, 183, 3, 0.35);
        background: linear-gradient(145deg, rgba(255, 183, 3, 0.08), transparent), #20202A;
      "
    >
      <h3 style="margin: 0 0 14px; color: #F8FAFC;">AI Review Insights</h3>

      <div style="margin-bottom: 16px;">
        <strong style="color: #FFB703;">Overall Summary</strong>
        <p style="margin: 8px 0 0; color: #CBD5E1; line-height: 1.7;">
          ${esc(insights.overall_summary || "No overall summary available.")}
        </p>
      </div>

      <div style="margin-bottom: 16px;">
        <strong style="color: #2DD4BF;">Positive Points</strong>
        <ul style="margin: 8px 0 0; padding-left: 20px; color: #CBD5E1; line-height: 1.7;">
          ${
            positivePoints.length
              ? positivePoints.map((p) => `<li>${esc(p)}</li>`).join("")
              : "<li>No positive points detected.</li>"
          }
        </ul>
      </div>

      <div style="margin-bottom: 16px;">
        <strong style="color: #F87171;">Negative Points</strong>
        <ul style="margin: 8px 0 0; padding-left: 20px; color: #CBD5E1; line-height: 1.7;">
          ${
            negativePoints.length
              ? negativePoints.map((p) => `<li>${esc(p)}</li>`).join("")
              : "<li>No negative points detected.</li>"
          }
        </ul>
      </div>

      <div>
        <strong style="color: #4CC9F0;">Final Opinion</strong>
        <p style="margin: 8px 0 0; color: #CBD5E1; line-height: 1.7;">
          ${esc(insights.final_opinion || "No final opinion generated.")}
        </p>
      </div>
    </div>
  `);
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

  reviewsListPage.innerHTML = reviews.map((r) => {
    const rating = r.rating ? `⭐ Review: ${esc(r.rating)}/10` : "⭐ Review: N/A";
    const titleLine = r.review_title
      ? `<div class="reviewTitle">${esc(r.review_title)}</div>`
      : "";

    return `
      <div class="reviewRow" data-rowid="${esc(r.row_id)}" role="button" tabindex="0">
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
  detailRatingBadge.textContent = "⭐ Review: …";
  detailRowIdBadge.textContent = `ID ${rowId}`;
  detailTitleRow.classList.add("hidden");
  detailTitle.textContent = "";
  detailOriginal.textContent = "Loading...";
  detailSummaryList.innerHTML = `<li class="muted">Loading…</li>`;
  detailHighlighted.innerHTML = `<span class="muted">Loading…</span>`;
  detailLegend.innerHTML = "";

  clearDynamicAnalysisCards();

  renderSentiment(null);
  renderConfidence(null);
  renderKeywords([]);
  renderInsights(null);

  const res = await fetch(`/api/review?row_id=${encodeURIComponent(rowId)}`);
  const data = await res.json();

  if (!data.ok) {
    detailOriginal.textContent = "";
    detailSummaryList.innerHTML = `<li class="muted">No summary produced.</li>`;
    detailHighlighted.innerHTML = `<span class="muted">Failed: ${esc(data.error || "")}</span>`;
    clearDynamicAnalysisCards();
    renderSentiment(null);
    renderConfidence(null);
    renderKeywords([]);
    renderInsights(null);
    return;
  }

  const ratingText = data.rating && String(data.rating).trim() !== ""
    ? `⭐ Review: ${data.rating}/10`
    : "⭐ Review: N/A";

  detailRatingBadge.textContent = ratingText;

  if (data.review_title && data.review_title.trim()) {
    detailTitleRow.classList.remove("hidden");
    detailTitle.textContent = data.review_title;
  } else {
    detailTitleRow.classList.add("hidden");
  }

  detailOriginal.textContent = data.original_text || "";

  const sents = data.summary_sentences || [];

  detailSummaryList.innerHTML = sents.length
    ? sents.map((s) => `<li>${esc(s)}</li>`).join("")
    : `<li class="muted">No summary produced.</li>`;

  const summaryText = data.summary_text || "";
  const ents = sanitizeEntities(data.entities_summary || []);

  detailHighlighted.innerHTML = summaryText
    ? renderHighlighted(summaryText, ents)
    : `<span class="muted">No summary text.</span>`;

  const labels = [...new Set(ents.map((e) => e.label))];

  detailLegend.innerHTML = labels.length
    ? labels.map((l) => `<span class="chip">${esc(String(l).replaceAll("_", " "))}</span>`).join("")
    : `<span class="muted">No entities found.</span>`;

  clearDynamicAnalysisCards();

  renderSentiment(data.sentiment);
  renderConfidence(data.confidence);
  renderKeywords(data.keywords || []);
  renderInsights(data.insights);
}

loadReviews();