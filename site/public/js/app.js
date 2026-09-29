import {
  generateQuestions,
  loadTaxonomy,
  matchSkills,
  parseText,
  scoreResume,
} from "./engine.js";

const REPO = "https://github.com/SJA-Pathway/AIPath";

const SAMPLE_CV = `Priya Sharma
priya.sharma@example.com | +91 98765 43210 | github.com/priyasharma

Summary
ML engineer with 3 years building NLP systems in Python.

Experience
Machine Learning Engineer, Acme Corp (2022 - present)
- Built a resume-ranking model in PyTorch that improved recruiter shortlist precision by 18%
- Deployed FastAPI inference services on AWS with Docker, cutting latency to 120 ms
- Led a team of 3 to migrate batch pipelines to Airflow
- Responsible for writing documentation

Education
B.Tech Computer Science, IIT Delhi, 2021

Skills
Python, SQL, PyTorch, scikit-learn, NLP, Docker, AWS, Git`;

const SAMPLE_JD = `Senior NLP Engineer

Requirements
- Strong Python and PyTorch
- Experience with NLP and LLMs in production
- Kubernetes and Docker

Nice to have
- LangChain or RAG pipelines
- AWS`;

const $ = (sel) => document.querySelector(sel);
const esc = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

const TRACK_LABEL = { ai: "AI feature", web: "Web development" };

const LEVEL_LABEL = {
  "good-first-issue": "Good first issue",
  intermediate: "Intermediate",
  advanced: "Advanced",
};

// ------------------------------------------------------------------ Demo

let tool = "match";

const chips = (items, cls) =>
  items.length
    ? `<ul class="chips">${items.map((s) => `<li class="chip ${cls}">${esc(s)}</li>`).join("")}</ul>`
    : `<p class="empty">None</p>`;
const group = (title, body) => `<div class="group"><h4>${esc(title)}</h4>${body}</div>`;

const RENDER = {
  match(cv, jd) {
    const r = matchSkills(cv, jd);
    return (
      `<div class="score"><b>${r.score}%</b><span>weighted skill coverage</span></div>` +
      group("Matched", chips(r.matched, "good")) +
      group("Missing: required", chips(r.missing_required, "bad")) +
      group("Missing: nice to have", chips(r.missing_optional, "warn")) +
      group("On your CV, not asked for", chips(r.extra, ""))
    );
  },
  score(cv, jd) {
    const r = scoreResume(cv, jd);
    const rows = r.checks
      .map(
        (c) => `<li><strong>${esc(c.name)}</strong><span class="pts">${c.points} / ${c.max_points}</span>
          <div class="bar"><span style="width:${(100 * c.points) / c.max_points}%"></span></div>
          <span class="fb">${esc(c.feedback)}</span></li>`,
      )
      .join("");
    return `<div class="score"><b>${r.score}</b><span>/ 100${jd.trim() ? ", scored against the job" : ""}</span></div><ul class="checks">${rows}</ul>`;
  },
  parse(cv) {
    return `<pre class="json"><code>${esc(JSON.stringify(parseText(cv), null, 2))}</code></pre>`;
  },
  interview(cv, jd) {
    const qs = generateQuestions($("#role").value || "this", cv, jd, 12);
    return `<ol class="qs">${qs
      .map(
        (q) => `<li><span class="cat">${esc(q.category)}</span><p>${esc(q.question)}</p><p class="guide">${esc(q.answer_guide)}</p></li>`,
      )
      .join("")}</ol>`;
  },
};

function run() {
  const cv = $("#cv").value;
  const jd = $("#jd").value;
  if (!cv.trim()) {
    $("#output").innerHTML = `<p class="empty">Paste a CV to get started.</p>`;
    return;
  }
  if (tool === "match" && !jd.trim()) {
    $("#output").innerHTML = `<p class="empty">The skill matcher needs a job description.</p>`;
    return;
  }
  $("#output").innerHTML = RENDER[tool](cv, jd);
}

function selectTool(next) {
  tool = next;
  document.querySelectorAll(".tabs button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tool === next)));
  $("#jd-wrap").hidden = next === "parse";
  $("#role-wrap").hidden = next !== "interview";
  run();
}

function resetSample() {
  $("#cv").value = SAMPLE_CV;
  $("#jd").value = SAMPLE_JD;
  run();
}

// ------------------------------------------------------------- Task board

let board = { features: [], tasks: [] };
let track = "";

function claimUrl(task) {
  const feature = board.features.find((f) => f.id === task.feature);
  const body =
    `I'd like to work on **${task.id}: ${task.title}** (${feature?.name ?? task.feature}).\n\n` +
    `> ${task.detail}\n\n` +
    `**My plan:**\n- \n\n` +
    `_Claimed from https://aipath.sjapathway.com/#tasks_`;
  const params = new URLSearchParams({ title: `[${task.id}] ${task.title}`, body });
  return `${REPO}/issues/new?${params}`;
}

function searchUrl(task) {
  return `${REPO}/issues?q=${encodeURIComponent(`is:issue "[${task.id}]"`)}`;
}

function renderTasks() {
  const feature = $("#f-feature").value;
  const level = $("#f-level").value;
  const status = $("#f-status").value;
  const list = board.tasks.filter(
    (t) => (!track || t.track === track) && (!feature || t.feature === feature) && (!level || t.level === level) && (!status || t.status === status),
  );
  $("#task-list").innerHTML = list.length
    ? list
        .map((t) => {
          const f = board.features.find((x) => x.id === t.feature);
          const action =
            t.status === "done"
              ? `<span class="badge done">Shipped</span>`
              : `<span><a href="${searchUrl(t)}" rel="noopener">Taken?</a> · <a class="btn small" href="${claimUrl(t)}" rel="noopener">Claim on GitHub</a></span>`;
          return `<li class="task ${t.status}">
            <header><span class="id">${esc(t.id)}</span><span class="badge ${t.level}">${LEVEL_LABEL[t.level] ?? esc(t.level)}</span><span class="badge track">${TRACK_LABEL[t.track] ?? esc(t.track)}</span></header>
            <h3>${esc(t.title)}</h3>
            <p>${esc(t.detail)}</p>
            <footer><span>${esc(f?.name ?? t.feature)}</span>${action}</footer>
          </li>`;
        })
        .join("")
    : `<li class="empty">No tasks match these filters.</li>`;
}

function renderFeatures() {
  $("#features-grid").innerHTML = board.features
    .map((f) => {
      const tasks = board.tasks.filter((t) => t.feature === f.id);
      const done = tasks.filter((t) => t.status === "done").length;
      return `<article class="feature">
        <span class="badge track">${TRACK_LABEL[f.track] ?? esc(f.track)}</span>
        <h3>${esc(f.name)}</h3>
        <p>${esc(f.summary)}</p>
        <div class="meta"><span>${done} of ${tasks.length} tasks done</span><span>${tasks.length - done} open</span></div>
        <div class="bar" role="img" aria-label="${done} of ${tasks.length} tasks done"><span style="width:${tasks.length ? (100 * done) / tasks.length : 0}%"></span></div>
        <a class="small" href="${REPO}/blob/main/${f.module}" rel="noopener"><code>${esc(f.module)}</code></a>
      </article>`;
    })
    .join("");
}

function renderStats() {
  const open = board.tasks.filter((t) => t.status === "open");
  const stats = [
    ["Features", board.features.length],
    ["Open tasks", open.length],
    ["Open AI tasks", open.filter((t) => t.track === "ai").length],
    ["Open web tasks", open.filter((t) => t.track === "web").length],
    ["Good first issues", open.filter((t) => t.level === "good-first-issue").length],
    ["Shipped", board.tasks.length - open.length],
  ];
  $("#stats").innerHTML = stats.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join("");
}

async function loadBoard() {
  board = await (await fetch("/data/tasks.json")).json();
  $("#f-feature").insertAdjacentHTML(
    "beforeend",
    board.features.map((f) => `<option value="${f.id}">${esc(f.name)}</option>`).join(""),
  );
  renderStats();
  renderFeatures();
  renderTasks();
}

// ------------------------------------------------------------------- Init

document.querySelectorAll(".tabs button").forEach((b) => b.addEventListener("click", () => selectTool(b.dataset.tool)));
$("#run").addEventListener("click", run);
$("#reset").addEventListener("click", resetSample);
document.querySelectorAll(".track-tabs button").forEach((b) =>
  b.addEventListener("click", () => {
    track = b.dataset.track;
    document.querySelectorAll(".track-tabs button").forEach((x) => x.setAttribute("aria-selected", String(x === b)));
    renderTasks();
  }),
);
["#f-feature", "#f-level", "#f-status"].forEach((id) => $(id).addEventListener("change", renderTasks));

$("#cv").value = SAMPLE_CV;
$("#jd").value = SAMPLE_JD;
loadBoard().catch(() => {
  $("#task-list").innerHTML = `<li class="empty">Couldn't load the task board. See <a href="${REPO}/blob/main/tasks.json">tasks.json</a>.</li>`;
});
loadTaxonomy()
  .then(() => selectTool("match"))
  .catch(() => {
    $("#output").innerHTML = `<p class="empty">Couldn't load the skills taxonomy.</p>`;
  });
