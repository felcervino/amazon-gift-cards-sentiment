"""Step 3: generate the self-contained results dashboard from Step 2's saved output.

The raw per-review records from output/step2_results.json are embedded directly into the
HTML as JSON data. Every statistic shown on the page (agreement rate, per-class accuracy,
confusion counts, class balance) is computed client-side, in the browser, from that same
embedded array, never precomputed in Python and typed into the template. This guarantees
every number on the page traces back to the exact saved file, not a separate summary that
could drift from it.

Review title/text is untrusted, user-generated content. It is embedded as escaped JSON
(</script>-safe) and rendered client-side using textContent/DOM APIs only, never innerHTML
with unescaped content, so it can never execute as markup.
"""
import json
import os

RESULTS_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "step2_results.json")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "dashboard", "dashboard.html")


def sanitize_records_for_embedding(records):
    """Defensive copy with non-finite numeric fields nulled out before JSON embedding.

    Found by the Step 3 Red Team pass: a corrupted source row with rating NaN/Infinity
    would, by default, cause json.dumps to emit the literal tokens NaN/Infinity, which are
    not valid JSON. A browser's JSON.parse on that single embedded array throws, uncaught,
    and silently breaks rendering for every row on the page, not just the bad one. Since
    such a rating is already treated as "flagged" by answer_key.py, it is nulled here too,
    rather than allowed to reach the page as an invalid token.
    """
    import math

    def clean_value(v):
        if isinstance(v, float) and not math.isfinite(v):
            return None
        return v

    return [{k: clean_value(v) for k, v in record.items()} for record in records]


def safe_json_for_script(obj) -> str:
    """JSON-encode for safe embedding inside an inline <script> tag.

    Escapes <, >, and & so a literal "</script>" sequence (which untrusted review text
    could contain, this is exactly the adversarial case Red Team tests) can never appear
    in the raw HTML and prematurely terminate the script block.

    allow_nan=False is defense in depth: if a non-finite float somehow still reaches this
    point (sanitize_records_for_embedding should have already caught it for review
    records, but this function is also used for the meta dict), fail loudly here with a
    clear Python-side error instead of silently emitting invalid JSON that only breaks at
    runtime in the browser.
    """
    s = json.dumps(obj, ensure_ascii=False, allow_nan=False)
    return s.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gift Card Review Sentiment Dashboard</title>
<style>
:root {
  /* Surfaces and ink: a warm ivory ground, paper-white cards, espresso text. */
  --bg: #faf6ef;
  --bg-wash: #f3ebdc;
  --surface: #ffffff;
  --surface-alt: #f5eee0;
  --surface-sunken: #f1ead9;
  --text: #2b241b;
  --text-muted: #6b5f4f;
  --text-faint: #9b8e7d;
  --border: #e6dcc8;
  --border-strong: #d9cbb2;
  --accent: #8a5a2b;
  --accent-deep: #6d451f;
  --accent-soft: #f0e2cc;
  --positive: #1f7a4d;
  --positive-bg: #e6f3ec;
  --positive-ring: #c2ddce;
  --negative: #b23a3a;
  --negative-bg: #fbeae7;
  --negative-ring: #efcbc4;

  /* Geometry */
  --radius: 14px;
  --radius-sm: 9px;
  --radius-pill: 999px;

  /* Elevation: warm-tinted, tight contact shadow plus a wide soft ambient one. */
  --shadow-sm: 0 1px 2px rgba(58, 44, 28, 0.05);
  --shadow-md: 0 1px 2px rgba(58, 44, 28, 0.05), 0 8px 20px -8px rgba(58, 44, 28, 0.13);
  --shadow-lg: 0 1px 2px rgba(58, 44, 28, 0.05), 0 16px 36px -12px rgba(58, 44, 28, 0.20);
  --shadow: var(--shadow-md);

  /* Motion */
  --ease: cubic-bezier(0.4, 0, 0.2, 1);
  --dur: 160ms;

  /* Typography */
  --ls-caps: 0.09em;
  --ls-caps-tight: 0.055em;
  --font-display: Georgia, 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', serif;
  --font-body: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  --font-mono: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
}

* { box-sizing: border-box; }

html { -webkit-text-size-adjust: 100%; }

body {
  margin: 0;
  background-color: var(--bg);
  background-image: linear-gradient(180deg, var(--bg-wash) 0%, var(--bg) 340px);
  background-repeat: no-repeat;
  color: var(--text);
  font-family: var(--font-body);
  font-size: 15px;
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

::selection { background: var(--accent-soft); color: var(--text); }

:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
  border-radius: 3px;
}

.page {
  max-width: 1100px;
  margin: 0 auto;
  padding: clamp(36px, 5.5vw, 60px) clamp(18px, 3vw, 28px) 104px;
}

/* ---------- Hero ---------- */

header.hero {
  margin-bottom: 52px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 34px;
}

.eyebrow {
  font-size: 12px;
  letter-spacing: var(--ls-caps);
  text-transform: uppercase;
  color: var(--accent);
  font-weight: 700;
  margin: 0 0 10px;
}

h1 {
  font-family: var(--font-display);
  font-size: clamp(30px, 4.4vw, 40px);
  line-height: 1.15;
  letter-spacing: -0.012em;
  margin: 0 0 14px;
  color: var(--text);
  font-weight: 400;
  text-wrap: balance;
}

.hero-sub {
  color: var(--text-muted);
  font-size: 16px;
  line-height: 1.6;
  max-width: 62ch;
  margin: 0;
}

.hero-meta {
  margin-top: 26px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  font-size: 12.5px;
  color: var(--text-muted);
}

.hero-meta span {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  padding: 5px 13px;
  box-shadow: var(--shadow-sm);
  /* The model id is a long unbroken token; let it break rather than force the
     page into horizontal scroll on a narrow viewport. */
  overflow-wrap: anywhere;
}

.hero-meta span strong {
  color: var(--text);
  font-weight: 600;
}

/* ---------- Section scaffolding ---------- */

section { margin-bottom: 56px; }
section:last-of-type { margin-bottom: 0; }

h2 {
  font-family: var(--font-display);
  font-weight: 400;
  font-size: 23px;
  letter-spacing: -0.008em;
  margin: 0 0 6px;
}

.section-note {
  color: var(--text-muted);
  font-size: 14px;
  line-height: 1.6;
  max-width: 68ch;
  margin: 0 0 22px;
}

/* ---------- Headline stat cards ---------- */

.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 16px;
}

.stat-card {
  position: relative;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 22px 22px;
  box-shadow: var(--shadow-md);
  overflow: hidden;
  transition: box-shadow var(--dur) var(--ease),
              transform var(--dur) var(--ease),
              border-color var(--dur) var(--ease);
}

/* Hairline of accent along the top edge, revealed on hover. */
.stat-card::before {
  content: "";
  position: absolute;
  inset: 0 0 auto 0;
  height: 2px;
  background: var(--accent);
  opacity: 0;
  transition: opacity var(--dur) var(--ease);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  border-color: var(--border-strong);
}

.stat-card:hover::before { opacity: 1; }

.stat-card .stat-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: var(--ls-caps);
  color: var(--text-muted);
  margin: 0 0 10px;
  font-weight: 700;
}

.stat-card .stat-value {
  font-family: var(--font-display);
  font-size: 34px;
  line-height: 1.05;
  letter-spacing: -0.015em;
  font-variant-numeric: tabular-nums;
  margin: 0;
  color: var(--text);
}

.stat-card .stat-sub {
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-muted);
  margin: 10px 0 0;
}

.skew-callout {
  margin-top: 18px;
  background: var(--accent-soft);
  border: 1px solid var(--border-strong);
  border-left: 3px solid var(--accent);
  border-radius: var(--radius-sm);
  padding: 15px 20px;
  font-size: 14px;
  line-height: 1.6;
  max-width: 88ch;
  color: var(--text);
}

/* ---------- Confusion matrix ---------- */

.confusion-wrap {
  display: flex;
  gap: 28px;
  flex-wrap: wrap;
  align-items: flex-start;
}

table.confusion {
  border-collapse: separate;
  border-spacing: 0;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow-md);
}

table.confusion caption {
  caption-side: top;
  text-align: left;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: var(--ls-caps);
  color: var(--text-muted);
  font-weight: 700;
  padding: 15px 20px 3px;
}

table.confusion th, table.confusion td {
  padding: 15px 24px;
  text-align: center;
  font-size: 15px;
  border-right: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

table.confusion tr > *:last-child { border-right: none; }
table.confusion tbody tr:last-child > * { border-bottom: none; }

table.confusion thead th,
table.confusion tbody th {
  background: var(--surface-alt);
  font-weight: 700;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: var(--ls-caps-tight);
  color: var(--text-muted);
  /* Deliberately NOT nowrap: on a narrow viewport these two-word labels must be
     free to wrap, or the matrix pushes the whole page into horizontal scroll. */
}

table.confusion tbody th { text-align: left; }

td.cell-correct, td.cell-mistake {
  font-weight: 700;
  font-size: 19px;
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum";
}

td.cell-correct { color: var(--positive); background: var(--positive-bg); }
td.cell-mistake { color: var(--negative); background: var(--negative-bg); }

.mistake-list {
  flex: 1;
  min-width: 260px;
}

.mistake-list ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mistake-list li {
  font-size: 14px;
  line-height: 1.5;
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--negative-ring);
  border-radius: var(--radius-sm);
  padding: 11px 15px;
  box-shadow: var(--shadow-sm);
  overflow-wrap: break-word;
  transition: border-left-color var(--dur) var(--ease),
              box-shadow var(--dur) var(--ease);
}

.mistake-list li:hover {
  border-left-color: var(--negative);
  box-shadow: var(--shadow-md);
}

/* ---------- Chips ---------- */

.chip {
  display: inline-block;
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: var(--ls-caps-tight);
  line-height: 1.6;
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  border: 1px solid transparent;
  text-transform: uppercase;
  white-space: nowrap;
}

.chip.positive {
  background: var(--positive-bg);
  color: var(--positive);
  border-color: var(--positive-ring);
}

.chip.negative {
  background: var(--negative-bg);
  color: var(--negative);
  border-color: var(--negative-ring);
}

/* ---------- Review table ---------- */

.table-controls {
  display: flex;
  gap: 14px;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.table-controls input[type="search"] {
  font-family: var(--font-body);
  font-size: 14px;
  padding: 9px 14px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-pill);
  min-width: 240px;
  background: var(--surface);
  color: var(--text);
  box-shadow: var(--shadow-sm);
  transition: border-color var(--dur) var(--ease), box-shadow var(--dur) var(--ease);
}

.table-controls input[type="search"]::placeholder { color: var(--text-faint); }

.table-controls input[type="search"]:hover { border-color: var(--accent); }

.table-controls input[type="search"]:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.table-controls .count {
  font-size: 13px;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

.review-table-wrap {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow-x: auto;
  box-shadow: var(--shadow-md);
}

table.reviews {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

table.reviews thead th {
  text-align: left;
  padding: 13px 16px;
  background: var(--surface-alt);
  font-size: 10.5px;
  text-transform: uppercase;
  letter-spacing: var(--ls-caps);
  color: var(--text-muted);
  font-weight: 700;
  white-space: nowrap;
  border-bottom: 1px solid var(--border-strong);
}

table.reviews tbody tr {
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background-color var(--dur) var(--ease);
}

table.reviews tbody tr:last-child { border-bottom: none; }
table.reviews tbody tr:hover { background: var(--surface-alt); }

/* Left rule: an accent bar on hover, a standing red bar on every mismatch, so a
   wrong row is legible structurally and not only by its background tint. */
table.reviews tbody tr > td:first-child {
  box-shadow: inset 3px 0 0 transparent;
  transition: box-shadow var(--dur) var(--ease);
}

table.reviews tbody tr:hover > td:first-child {
  box-shadow: inset 3px 0 0 var(--accent);
}

table.reviews td {
  padding: 13px 16px;
  vertical-align: top;
}

td.col-rating {
  white-space: nowrap;
  color: var(--accent);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

/* break-word, not anywhere: `anywhere` also shrinks the column's min-content width,
   which makes the auto table layout snap ordinary titles mid-word. break-word still
   rescues a single unbreakable token from blowing out the layout. */
td.col-title {
  font-weight: 600;
  max-width: 220px;
  overflow-wrap: break-word;
}

td.col-text {
  color: var(--text-muted);
  max-width: 360px;
  overflow-wrap: break-word;
}

/* Muted by default so the common "correct" tick recedes; a mismatch row promotes
   its own mark to the alert colour below. Null/flagged rows stay neutral. */
td.col-match {
  text-align: center;
  font-size: 16px;
  line-height: 1.4;
  color: var(--text-faint);
}

/* These selectors are deliberately qualified up to `table.reviews tbody` so they
   outrank the generic row and row-hover rules above; without that, the hover rule
   wins on specificity and a mismatch row loses its red treatment while hovered. */
table.reviews tbody tr.row-mismatch { background: var(--negative-bg); }
table.reviews tbody tr.row-mismatch:hover { background: #f8ded9; }

table.reviews tbody tr.row-mismatch > td:first-child,
table.reviews tbody tr.row-mismatch:hover > td:first-child {
  box-shadow: inset 3px 0 0 var(--negative);
}

table.reviews tbody tr.row-mismatch td.col-match {
  color: var(--negative);
  font-weight: 700;
}

/* ---------- Expanded detail row ---------- */

.detail-row > td {
  background: var(--surface-sunken);
  padding: 18px 20px;
  font-size: 13px;
  box-shadow: inset 3px 0 0 var(--accent), inset 0 1px 0 var(--border);
  /* No fill-mode: the resting style must be the visible one, so the panel still shows
     in any context that does not run CSS animations (print, snapshot renderers). */
  animation: detail-in 180ms var(--ease);
}

@keyframes detail-in {
  from { opacity: 0; transform: translateY(-3px); }
  to { opacity: 1; transform: none; }
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.detail-grid h4 {
  margin: 0 0 8px;
  font-size: 10.5px;
  text-transform: uppercase;
  letter-spacing: var(--ls-caps);
  font-weight: 700;
  color: var(--text-muted);
}

.detail-grid pre {
  white-space: pre-wrap;
  word-break: break-word;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.6;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  margin: 0;
  box-shadow: var(--shadow-sm);
}

/* ---------- Footer ---------- */

footer {
  margin-top: 72px;
  border-top: 1px solid var(--border);
  padding-top: 22px;
  font-size: 13px;
  line-height: 1.65;
  color: var(--text-muted);
}

footer p { margin: 0; max-width: 78ch; }

footer a {
  color: var(--accent);
  text-decoration-color: var(--border-strong);
  text-underline-offset: 2px;
  transition: color var(--dur) var(--ease), text-decoration-color var(--dur) var(--ease);
}

footer a:hover { color: var(--accent-deep); text-decoration-color: currentColor; }

footer code {
  font-family: var(--font-mono);
  font-size: 12px;
  background: var(--surface-alt);
  border: 1px solid var(--border);
  border-radius: 5px;
  padding: 1px 5px;
}

/* ---------- Responsive ---------- */

@media (max-width: 900px) {
  .confusion-wrap { gap: 24px; }
  table.confusion { width: 100%; }
  table.confusion th, table.confusion td { padding: 13px 16px; }
}

@media (max-width: 640px) {
  body { font-size: 14.5px; }
  header.hero { margin-bottom: 40px; padding-bottom: 28px; }
  .hero-sub { font-size: 15px; }
  section { margin-bottom: 44px; }
  .confusion-wrap { flex-direction: column; }
  table.confusion { width: 100%; }
  table.confusion th, table.confusion td { padding: 12px 10px; }
  table.confusion thead th, table.confusion tbody th { letter-spacing: 0.03em; }
  .stat-card .stat-value { font-size: 30px; }
  td.col-text, th.col-text { display: none; }
  .detail-grid { grid-template-columns: 1fr; }
  .table-controls input[type="search"] { min-width: 0; flex: 1 1 200px; }
}

@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  .stat-card:hover { transform: none; }
}
</style>
</head>
<body>
<div class="page">
  <header class="hero">
    <p class="eyebrow">MBAX 6418, Assignment 1</p>
    <h1>Gift Card Review Sentiment Dashboard</h1>
    <p class="hero-sub">How well does a hosted LLM classify Amazon Gift Card reviews as
      POSITIVE or NEGATIVE, checked against the reviewer's own star rating? The model
      never sees the rating; it is used only afterward to judge the model's answers.</p>
    <div class="hero-meta">
      <span>Model: <strong id="meta-model"></strong></span>
      <span>Temperature: <strong id="meta-temp"></strong></span>
      <span>Batch: <strong>first 100 rows</strong> of Gift_Cards.jsonl.gz</span>
      <span>Source: <strong>output/step2_results.json</strong></span>
    </div>
  </header>

  <section id="headline-section">
    <h2>Headline numbers</h2>
    <p class="section-note">Computed live from the embedded review records below, the same
      records shown in the table further down the page.</p>
    <div class="stat-grid" id="stat-grid"></div>
    <div class="skew-callout" id="skew-callout"></div>
  </section>

  <section id="confusion-section">
    <h2>Where mistakes cluster</h2>
    <p class="section-note">A right/wrong total hides which direction the model tends to
      get wrong. This breaks it out by class.</p>
    <div class="confusion-wrap">
      <table class="confusion" id="confusion-table">
        <caption>Answer key (rows) vs. model prediction (columns)</caption>
      </table>
      <div class="mistake-list">
        <h3 style="font-family:var(--font-display);font-weight:400;font-size:16px;margin:0 0 10px;">All mismatches</h3>
        <ul id="mistake-list"></ul>
      </div>
    </div>
  </section>

  <section id="table-section">
    <h2>Every review</h2>
    <p class="section-note">Click a row to see the full text and the model's raw response.</p>
    <div class="table-controls">
      <input type="search" id="search-box" placeholder="Search title or text...">
      <span class="count" id="row-count"></span>
    </div>
    <div class="review-table-wrap">
      <table class="reviews" id="review-table">
        <thead>
          <tr>
            <th class="col-rating">Rating</th>
            <th class="col-title">Title</th>
            <th class="col-text">Text</th>
            <th class="col-answer">Answer key</th>
            <th class="col-model">Model said</th>
            <th class="col-match">Match</th>
          </tr>
        </thead>
        <tbody id="review-tbody"></tbody>
      </table>
    </div>
  </section>

  <footer>
    <p>Data: Amazon Reviews '23 (Gift Cards category), McAuley Lab, UC San Diego.
      <a href="https://amazon-reviews-2023.github.io" target="_blank" rel="noopener">amazon-reviews-2023.github.io</a>.
      Numbers on this page are computed in the browser from the review records embedded
      in this file, generated from <code>output/step2_results.json</code>.</p>
  </footer>
</div>

<script id="review-data" type="application/json">__REVIEW_DATA_JSON__</script>
<script id="meta-data" type="application/json">__META_DATA_JSON__</script>
<script>
(function () {
  "use strict";

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  // Some source review text contains literal HTML entities (e.g. "&#34;", "<br />") from
  // the raw dataset. Decode entities for readability using the textarea trick: setting
  // innerHTML on a <textarea> parses in RCDATA mode, which decodes character references
  // but never parses tags as elements, so this cannot execute markup. The decoded string
  // is still only ever assigned via textContent below, never innerHTML.
  var decoderEl = document.createElement("textarea");
  function decodeEntities(s) {
    if (!s) return s;
    decoderEl.innerHTML = s;
    return decoderEl.value;
  }

  var records = JSON.parse(document.getElementById("review-data").textContent);
  var meta = JSON.parse(document.getElementById("meta-data").textContent);

  document.getElementById("meta-model").textContent = meta.model;
  document.getElementById("meta-temp").textContent = String(meta.temperature);

  // All statistics below are computed directly from `records`, the same array
  // rendered into the table. No number here is typed in separately.
  var valid = records.filter(function (r) {
    return r.answer_key_status === "ok" && r.parsed_status === "ok";
  });

  var nValid = valid.length;
  var nMatch = valid.filter(function (r) { return r.match; }).length;
  var agreementRate = nValid ? nMatch / nValid : null;

  var classCounts = { POSITIVE: 0, NEGATIVE: 0 };
  valid.forEach(function (r) { classCounts[r.answer_key_label]++; });

  var perClass = {};
  ["POSITIVE", "NEGATIVE"].forEach(function (label) {
    var rows = valid.filter(function (r) { return r.answer_key_label === label; });
    var correct = rows.filter(function (r) { return r.match; }).length;
    perClass[label] = { n: rows.length, correct: correct, accuracy: rows.length ? correct / rows.length : null };
  });

  function pct(x) { return x === null ? "n/a" : (x * 100).toFixed(1) + "%"; }

  var statGrid = document.getElementById("stat-grid");
  var stats = [
    { label: "Overall agreement", value: pct(agreementRate), sub: nMatch + " of " + nValid + " reviews matched the rating-derived answer key" },
    { label: "POSITIVE accuracy", value: pct(perClass.POSITIVE.accuracy), sub: perClass.POSITIVE.correct + " of " + perClass.POSITIVE.n + " POSITIVE reviews correctly identified" },
    { label: "NEGATIVE accuracy", value: pct(perClass.NEGATIVE.accuracy), sub: perClass.NEGATIVE.correct + " of " + perClass.NEGATIVE.n + " NEGATIVE reviews correctly identified" },
    { label: "Class balance", value: classCounts.POSITIVE + " / " + classCounts.NEGATIVE, sub: "POSITIVE / NEGATIVE by the rating answer key" }
  ];
  stats.forEach(function (s) {
    var card = document.createElement("div");
    card.className = "stat-card";
    var label = document.createElement("p"); label.className = "stat-label"; label.textContent = s.label;
    var value = document.createElement("p"); value.className = "stat-value"; value.textContent = s.value;
    var sub = document.createElement("p"); sub.className = "stat-sub"; sub.textContent = s.sub;
    card.appendChild(label); card.appendChild(value); card.appendChild(sub);
    statGrid.appendChild(card);
  });

  var skewPct = nValid ? (classCounts.POSITIVE / nValid * 100).toFixed(1) : "n/a";
  document.getElementById("skew-callout").textContent =
    skewPct + "% of this batch is POSITIVE by the rating answer key. The data is heavily " +
    "skewed toward high ratings, a high overall agreement number on its own does not mean " +
    "the model is strong on the minority NEGATIVE class; check the per-class numbers above.";

  // Confusion matrix, computed from the same records.
  var confusion = {
    POSITIVE: { POSITIVE: 0, NEGATIVE: 0 },
    NEGATIVE: { POSITIVE: 0, NEGATIVE: 0 }
  };
  valid.forEach(function (r) {
    confusion[r.answer_key_label][r.parsed_label]++;
  });

  var confTable = document.getElementById("confusion-table");
  var thead = document.createElement("thead");
  var headRow = document.createElement("tr");
  headRow.appendChild(document.createElement("th"));
  ["Predicted POSITIVE", "Predicted NEGATIVE"].forEach(function (h) {
    var th = document.createElement("th"); th.textContent = h; headRow.appendChild(th);
  });
  thead.appendChild(headRow);
  confTable.appendChild(thead);

  var tbody = document.createElement("tbody");
  ["POSITIVE", "NEGATIVE"].forEach(function (actual) {
    var row = document.createElement("tr");
    var rowHeader = document.createElement("th");
    rowHeader.textContent = "Actually " + actual;
    row.appendChild(rowHeader);
    ["POSITIVE", "NEGATIVE"].forEach(function (predicted) {
      var td = document.createElement("td");
      td.textContent = confusion[actual][predicted];
      td.className = (actual === predicted) ? "cell-correct" : "cell-mistake";
      row.appendChild(td);
    });
    tbody.appendChild(row);
  });
  confTable.appendChild(tbody);

  var mismatches = valid.filter(function (r) { return !r.match; });
  var mistakeList = document.getElementById("mistake-list");
  if (mismatches.length === 0) {
    var li = document.createElement("li");
    li.textContent = "No mismatches in this batch.";
    mistakeList.appendChild(li);
  } else {
    mismatches.forEach(function (r) {
      var li = document.createElement("li");
      var titleSpan = document.createElement("strong");
      titleSpan.textContent = decodeEntities(r.title) || "(no title)";
      li.appendChild(titleSpan);
      var detail = document.createElement("div");
      detail.style.color = "var(--text-muted)";
      detail.style.marginTop = "4px";
      detail.textContent = "rating " + r.rating + ": answer key " + r.answer_key_label +
        ", model said " + r.parsed_label;
      li.appendChild(detail);
      mistakeList.appendChild(li);
    });
  }

  // Full review table, built with textContent everywhere. Untrusted review title/text
  // is never assigned via innerHTML, so it can never execute as markup.
  var tbodyEl = document.getElementById("review-tbody");
  var rowCountEl = document.getElementById("row-count");
  var searchBox = document.getElementById("search-box");

  function truncate(s, n) {
    s = s || "";
    return s.length > n ? s.slice(0, n) + "..." : s;
  }

  function renderTable(filterText) {
    tbodyEl.innerHTML = "";
    var filtered = records.filter(function (r) {
      if (!filterText) return true;
      var haystack = ((r.title || "") + " " + (r.text || "")).toLowerCase();
      return haystack.indexOf(filterText.toLowerCase()) !== -1;
    });

    filtered.forEach(function (r) {
      var tr = document.createElement("tr");
      if (r.match === false) tr.className = "row-mismatch";

      var tdRating = document.createElement("td");
      tdRating.className = "col-rating";
      tdRating.textContent = r.rating != null ? r.rating + " star" + (r.rating === 1 ? "" : "s") : "n/a";
      tr.appendChild(tdRating);

      var tdTitle = document.createElement("td");
      tdTitle.className = "col-title";
      tdTitle.textContent = decodeEntities(r.title) || "(no title)";
      tr.appendChild(tdTitle);

      var tdText = document.createElement("td");
      tdText.className = "col-text";
      tdText.textContent = truncate(decodeEntities(r.text), 90);
      tr.appendChild(tdText);

      var tdAnswer = document.createElement("td");
      var answerChip = document.createElement("span");
      answerChip.className = "chip " + (r.answer_key_label === "POSITIVE" ? "positive" : "negative");
      answerChip.textContent = r.answer_key_label || r.answer_key_status;
      tdAnswer.appendChild(answerChip);
      tr.appendChild(tdAnswer);

      var tdModel = document.createElement("td");
      var modelChip = document.createElement("span");
      modelChip.className = "chip " + (r.parsed_label === "POSITIVE" ? "positive" : "negative");
      modelChip.textContent = r.parsed_label || r.parsed_status;
      tdModel.appendChild(modelChip);
      tr.appendChild(tdModel);

      var tdMatch = document.createElement("td");
      tdMatch.className = "col-match";
      tdMatch.textContent = r.match === true ? "✓" : (r.match === false ? "✗" : "-");
      tr.appendChild(tdMatch);

      tr.addEventListener("click", function () { toggleDetail(tr, r); });
      tbodyEl.appendChild(tr);
    });

    rowCountEl.textContent = "Showing " + filtered.length + " of " + records.length + " reviews";
  }

  function toggleDetail(tr, record) {
    var next = tr.nextElementSibling;
    if (next && next.classList.contains("detail-row")) {
      next.remove();
      return;
    }
    var existingDetail = document.querySelector(".detail-row");
    if (existingDetail) existingDetail.remove();

    var detailRow = document.createElement("tr");
    detailRow.className = "detail-row";
    var td = document.createElement("td");
    td.colSpan = 6;

    var grid = document.createElement("div");
    grid.className = "detail-grid";

    var textBlock = document.createElement("div");
    var textHeader = document.createElement("h4"); textHeader.textContent = "Full review text";
    var textPre = document.createElement("pre"); textPre.textContent = decodeEntities(record.text) || "";
    textBlock.appendChild(textHeader); textBlock.appendChild(textPre);

    var respBlock = document.createElement("div");
    var respHeader = document.createElement("h4"); respHeader.textContent = "Raw model response";
    var respPre = document.createElement("pre"); respPre.textContent = record.raw_model_response || "";
    respBlock.appendChild(respHeader); respBlock.appendChild(respPre);

    grid.appendChild(textBlock);
    grid.appendChild(respBlock);
    td.appendChild(grid);
    detailRow.appendChild(td);
    tr.parentNode.insertBefore(detailRow, tr.nextSibling);
  }

  searchBox.addEventListener("input", function () { renderTable(searchBox.value); });

  renderTable("");
})();
</script>
</body>
</html>
"""


DEFAULT_META = {
    "model": "cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit",
    "temperature": 0,
}


def render_dashboard(records, meta=None) -> str:
    """Render the dashboard HTML for a given list of review records. Used both by the
    normal generator (below) and by the Step 3 Red Team XSS test, which runs adversarial
    records through this exact same function, the actual rendering pipeline."""
    meta = meta or DEFAULT_META
    clean_records = sanitize_records_for_embedding(records)
    html = HTML_TEMPLATE.replace("__REVIEW_DATA_JSON__", safe_json_for_script(clean_records))
    html = html.replace("__META_DATA_JSON__", safe_json_for_script(meta))
    return html


def main():
    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)

    html = render_dashboard(records)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    # errors="replace": found by the Step 3 Red Team pass, a strict utf-8 write crashes
    # outright on an unpaired UTF-16 surrogate in source review text (which non-strict
    # json.loads will accept from a malformed dataset line). Replacing with U+FFFD
    # degrades gracefully instead of crashing generation entirely.
    with open(OUTPUT_PATH, "w", encoding="utf-8", errors="replace") as f:
        f.write(html)

    print(f"Dashboard written to {OUTPUT_PATH} ({len(html)} bytes), embedding {len(records)} review records.")


if __name__ == "__main__":
    main()
