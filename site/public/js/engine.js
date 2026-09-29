// Browser port of the aipath Python package, used by the live demo.
// Keep behaviour in sync with aipath/*.py — parity tests are task WEB-2.

const WORD = "[\\w+#]";
const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

let TAXONOMY = [];

export async function loadTaxonomy(url = "/data/skills.json") {
  const data = await (await fetch(url)).json();
  TAXONOMY = Object.entries(data.skills).map(([name, info]) => ({
    name,
    category: info.category,
    terms: [name, ...(info.aliases || [])].map((term) => ({
      term,
      re: new RegExp(`(?<!${WORD})${escapeRe(term)}(?!${WORD})`, "gi"),
    })),
  }));
}

const shortTermOk = (term, found, canonical) =>
  term.length > 2 || found === found.toUpperCase() || found === canonical;

export function extractSkills(text) {
  const found = [];
  for (const skill of TAXONOMY) {
    const hit = skill.terms.some(({ term, re }) =>
      [...text.matchAll(re)].some((m) => shortTermOk(term, m[0], skill.name)),
    );
    if (hit) found.push(skill.name);
  }
  return found;
}

const categoryOf = (name) => TAXONOMY.find((s) => s.name === name)?.category;

// ---------------------------------------------------------------- CV parser

const EMAIL_RE = /[\w.+-]+@[\w-]+(?:\.[\w-]+)+/;
const PHONE_RE = /\+?\d[\d\s().-]{7,}\d/;
const URL_RE = /(?:https?:\/\/|www\.)\S+|(?:linkedin\.com|github\.com)\/\S+/gi;

const SECTION_HEADINGS = {
  summary: "summary", profile: "summary", about: "summary", "about me": "summary", objective: "summary",
  experience: "experience", "work experience": "experience", "professional experience": "experience",
  employment: "experience", "employment history": "experience",
  education: "education", "academic background": "education",
  skills: "skills", "technical skills": "skills", "core skills": "skills",
  projects: "projects", "personal projects": "projects",
  certifications: "certifications", certificates: "certifications",
  awards: "awards", publications: "publications",
};

function headingKey(line) {
  const cleaned = line.toLowerCase().replace(/[^a-z ]/g, "").trim();
  if (!cleaned || cleaned.length > 30) return null;
  return SECTION_HEADINGS[cleaned] || null;
}

function guessName(lines) {
  for (const line of lines.slice(0, 5)) {
    if (EMAIL_RE.test(line) || PHONE_RE.test(line) || new RegExp(URL_RE.source, "i").test(line)) continue;
    if (headingKey(line)) continue;
    const words = line.split(/\s+/);
    if (words.length > 1 && words.length <= 4 && words.every((w) => /^[A-Z]/.test(w))) return line;
  }
  return null;
}

export function parseText(text) {
  const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  const sections = {};
  let current = null;
  for (const line of lines) {
    const key = headingKey(line);
    if (key) {
      current = key;
      sections[key] ??= [];
    } else if (current) {
      sections[current].push(line.replace(/^[-•*·\s]+/, "").trim());
    }
  }
  return {
    name: guessName(lines),
    email: text.match(EMAIL_RE)?.[0] ?? null,
    phone: text.match(PHONE_RE)?.[0].trim() ?? null,
    links: [...text.matchAll(URL_RE)].map((m) => m[0].replace(/[.,)]+$/, "")),
    skills: extractSkills(text),
    sections,
    word_count: text.split(/\s+/).filter(Boolean).length,
  };
}

// ------------------------------------------------------------ Skill matcher

const OPTIONAL_MARKERS = /nice[\s-]to[\s-]have|preferred|bonus|plus|desirable|good to have/i;
const REQUIRED_MARKERS = /requirements|required|must[\s-]have|qualifications|you have|what you.?ll need/i;
const OPTIONAL_WEIGHT = 0.5;

export function splitJobSkills(jd) {
  const required = [];
  const optional = [];
  let inOptional = false;
  for (const line of jd.split(/\r?\n/)) {
    if (line.split(/\s+/).filter(Boolean).length <= 6) {
      if (OPTIONAL_MARKERS.test(line)) inOptional = true;
      else if (REQUIRED_MARKERS.test(line)) inOptional = false;
    }
    const target = inOptional ? optional : required;
    for (const s of extractSkills(line)) {
      if (!required.includes(s) && !optional.includes(s)) target.push(s);
    }
  }
  return { required, optional };
}

export function matchSkills(cvText, jd) {
  const cv = new Set(extractSkills(cvText));
  const { required, optional } = splitJobSkills(jd);
  const total = required.length + OPTIONAL_WEIGHT * optional.length;
  const earned =
    required.filter((s) => cv.has(s)).length + OPTIONAL_WEIGHT * optional.filter((s) => cv.has(s)).length;
  const wanted = new Set([...required, ...optional]);
  return {
    score: total ? Math.round((100 * earned) / total) : 0,
    matched: [...required, ...optional].filter((s) => cv.has(s)),
    missing_required: required.filter((s) => !cv.has(s)),
    missing_optional: optional.filter((s) => !cv.has(s)),
    extra: [...cv].filter((s) => !wanted.has(s)).sort(),
  };
}

// ------------------------------------------------------------ Resume scorer

export const ACTION_VERBS = new Set(
  ("achieved automated built created cut delivered deployed designed developed drove grew implemented " +
    "improved increased launched led managed mentored migrated optimised optimized owned reduced " +
    "refactored scaled shipped trained").split(" "),
);
const METRIC_RE = /\d+(?:\.\d+)?\s*(?:%|x\b|k\b|m\b|ms\b|users|customers|hours|days)|[$£€₹]\s?\d/i;
const CORE_SECTIONS = ["experience", "education", "skills"];

const firstWord = (b) => (b.split(/\s+/)[0] || "").toLowerCase().replace(/[,.]/g, "");
const bulletsOf = (cv) => [...(cv.sections.experience || []), ...(cv.sections.projects || [])];
const check = (name, points, max_points, feedback) => ({ name, points, max_points, feedback });
const title = (s) => s[0].toUpperCase() + s.slice(1);

export function scoreResume(cvText, jd) {
  const cv = parseText(cvText);
  const checks = [];

  const have = [cv.email && "email", cv.phone && "phone"].filter(Boolean);
  checks.push(
    check(
      "Contact details",
      have.length === 2 ? 10 : have.length ? 5 : 0,
      10,
      have.length === 2
        ? "Email and phone are both present."
        : have.length
          ? `Add your ${have.includes("email") ? "phone number" : "email address"}: recruiters and ATS filters look for both.`
          : "No email or phone found. Put both at the top of the CV.",
    ),
  );

  const missing = CORE_SECTIONS.filter((s) => !(s in cv.sections));
  checks.push(
    check(
      "Standard sections",
      Math.round((20 * (CORE_SECTIONS.length - missing.length)) / CORE_SECTIONS.length),
      20,
      missing.length
        ? `Add clearly labelled section(s): ${missing.map(title).join(", ")}. ATS parsers rely on standard headings.`
        : "Experience, Education and Skills sections are all clearly headed.",
    ),
  );

  const words = cv.word_count;
  checks.push(
    words >= 300 && words <= 900
      ? check("Length", 10, 10, `${words} words: a good length for one to two pages.`)
      : words < 300
        ? check("Length", words >= 150 ? 4 : 0, 10, `Only ${words} words. Expand your experience with concrete outcomes.`)
        : check("Length", 5, 10, `${words} words is long. Trim older or less relevant roles to stay under ~900.`),
  );

  const bullets = bulletsOf(cv);
  if (!bullets.length) {
    checks.push(check("Action verbs", 0, 15, "No experience or project bullets found to evaluate."));
    checks.push(check("Quantified impact", 0, 20, "No experience or project bullets found to evaluate."));
  } else {
    const strong = bullets.filter((b) => ACTION_VERBS.has(firstWord(b))).length;
    const r1 = strong / bullets.length;
    checks.push(
      check(
        "Action verbs",
        Math.round(15 * Math.min(r1 / 0.6, 1)),
        15,
        r1 >= 0.6
          ? `${strong}/${bullets.length} bullets start with a strong action verb.`
          : `Only ${strong}/${bullets.length} bullets start with an action verb. Lead with verbs like 'Built', 'Reduced', 'Shipped'.`,
      ),
    );
    const quantified = bullets.filter((b) => METRIC_RE.test(b)).length;
    const r2 = quantified / bullets.length;
    checks.push(
      check(
        "Quantified impact",
        Math.round(20 * Math.min(r2 / 0.5, 1)),
        20,
        r2 >= 0.5
          ? `${quantified}/${bullets.length} bullets include a number. Good, measurable impact.`
          : `Only ${quantified}/${bullets.length} bullets include a metric. Add numbers (%, users, time saved, revenue).`,
      ),
    );
  }

  if (jd && jd.trim()) {
    const m = matchSkills(cvText, jd);
    const miss = m.missing_required.slice(0, 5);
    checks.push(
      check(
        "Job keyword match",
        Math.round((25 * m.score) / 100),
        25,
        `Covers ${m.score}% of the job's skills.` + (miss.length ? ` Missing required: ${miss.join(", ")}.` : ""),
      ),
    );
  } else {
    const n = cv.skills.length;
    checks.push(
      check(
        "Skills coverage",
        Math.round(25 * Math.min(n / 10, 1)),
        25,
        n >= 10
          ? `${n} recognised skills listed.`
          : `Only ${n} recognised skills found. List your tools and technologies explicitly (and paste a job description for a targeted score).`,
      ),
    );
  }

  const total = checks.reduce((a, c) => a + c.points, 0);
  const max = checks.reduce((a, c) => a + c.max_points, 0);
  return { score: Math.round((100 * total) / max), checks };
}

// ------------------------------------------------- Interview questions

const q = (category, question, answer_guide) => ({ category, question, answer_guide });

const BEHAVIOURAL = [
  q("behavioural", "Tell me about a time you disagreed with a technical decision. What did you do?",
    "Use STAR: the Situation, your Task, the Actions you took to make your case with evidence, and the Result, including what you learned."),
  q("behavioural", "Describe a project that failed or slipped. What would you do differently?",
    "Own your part, be specific about the root cause, and end with a concrete change you've since made to how you work."),
  q("behavioural", "How do you explain a model's limitations to a non-technical stakeholder?",
    "Pick a real example. Show you translate metrics into business risk and suggest mitigations, not just caveats."),
];

const TECHNICAL_BY_CATEGORY = {
  ai: "How have you evaluated {skill} systems in practice? Which metrics did you use and why?",
  framework: "What's a non-obvious pitfall you've hit with {skill}, and how did you work around it?",
  language: "What {skill} feature or idiom do you rely on most, and when would you avoid it?",
  tooling: "Walk me through how you've used {skill} in a production workflow.",
  soft: "Give an example that shows your {skill} made a measurable difference to a team outcome.",
};

export function generateQuestions(role, cvText, jd, limit = 10) {
  const out = [
    q("behavioural", `Why this ${role} role, and why now?`,
      "Connect two or three specific things about the role to evidence from your background. Avoid generic enthusiasm."),
  ];
  const cv = cvText && cvText.trim() ? parseText(cvText) : null;

  if (cv) {
    const bullets = (cv.sections.experience || []).filter((b) => ACTION_VERBS.has(firstWord(b)));
    bullets
      .sort((a, b) => Number(METRIC_RE.test(b)) - Number(METRIC_RE.test(a)))
      .slice(0, 3)
      .filter((b) => b.split(/\s+/).length >= 5)
      .forEach((b) =>
        out.push(q("experience", `Your CV says: "${b}". Walk me through how you did that.`,
          "Explain the starting point, the approach you chose over alternatives, your personal contribution, and how the result was measured.")),
      );
  }

  let skills = cv ? cv.skills : [];
  if (cv && jd && jd.trim()) {
    const m = matchSkills(cvText, jd);
    m.missing_required.slice(0, 2).forEach((s) =>
      out.push(q("gap", `This role needs ${s}, which isn't on your CV. How would you get productive with it?`,
        "Be honest about the gap. Point to the closest thing you have done and give a concrete ramp-up plan.")),
    );
    skills = m.matched;
  }

  skills.slice(0, 4).forEach((s) => {
    const tpl = TECHNICAL_BY_CATEGORY[categoryOf(s)] || TECHNICAL_BY_CATEGORY.tooling;
    out.push(q("technical", tpl.replace("{skill}", s),
      `Anchor your answer in a specific project where you used ${s}. Interviewers probe for depth, not breadth.`));
  });

  return [...out, ...BEHAVIOURAL].slice(0, limit);
}
