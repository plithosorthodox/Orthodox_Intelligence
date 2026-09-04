"use strict";

const statusNode = document.querySelector("#status");
const versionsNode = document.querySelector("#versions");
const messagesNode = document.querySelector("#messages");
const form = document.querySelector("#ask-form");
const questionNode = document.querySelector("#question");
const corpusDescription = document.querySelector("#corpus-description");
const corpusSummary = document.querySelector("#corpus-summary");
const welcomeMessage = document.querySelector("#welcome-message");
const evaluationPanel = document.querySelector("#evaluation-panel");
const evaluationSummary = document.querySelector("#evaluation-summary");
const evaluationLimit = document.querySelector("#evaluation-limit");
const evaluationResults = document.querySelector("#evaluation-results");
const calendarPanel = document.querySelector("#calendar-panel");
const calendarDate = document.querySelector("#calendar-date");
const calendarMode = document.querySelector("#calendar-mode");
const calendarResult = document.querySelector("#calendar-result");
const calendarGo = document.querySelector("#calendar-go");
let calendarDay = null;

function element(name, className, text) {
  const node = document.createElement(name);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function request(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `Request failed: ${response.status}`);
  return payload;
}

function showVersions(versions) {
  versionsNode.replaceChildren();
  for (const [name, value] of Object.entries(versions)) {
    versionsNode.append(element("dt", "", name.replaceAll("_", " ")));
    versionsNode.append(element("dd", "", value));
  }
}

function addUserMessage(text) {
  const article = element("article", "message user");
  article.append(element("p", "", text));
  messagesNode.append(article);
}

function addAnswer(answer) {
  const article = element("article", "message assistant");
  article.append(element("p", "classification", `${answer.response_class} · ${answer.intent}`));
  article.append(element("p", "", answer.text));
  for (const evidence of answer.evidence || []) {
    const card = element("section", "evidence-card");
    card.append(element("h3", "", evidence.title));
    card.append(element("p", "classification", evidence.source_class));
    card.append(element("blockquote", "", evidence.display_text));
    const locator = evidence.source_locator ? ` · ${evidence.source_locator}` : "";
    card.append(element("cite", "", `${evidence.citation_label} · ${evidence.segment_id}${locator}`));
    article.append(card);
  }
  messagesNode.append(article);
  messagesNode.scrollTop = messagesNode.scrollHeight;
}

function renderCalendar() {
  if (!calendarDay) return;
  const value = calendarDay(calendarDate.value, {cal: calendarMode.value, lang: "en", juris: "greek"});
  calendarResult.replaceChildren();
  if (!value) {
    calendarResult.append(element("p", "", "Invalid date."));
    return;
  }
  const liturgicalDate = value.calendar === "old" ? value.julian : value.date;
  calendarResult.append(element("h3", "", value.headline || value.day_name || value.date));
  calendarResult.append(element("p", "classification", `${value.calendar === "old" ? "Old Calendar · Julian" : "New Calendar · Revised Julian"} · liturgical date ${liturgicalDate}`));
  if (value.commemorations && value.commemorations.length) {
    calendarResult.append(element("p", "", value.commemorations.map((item) => item.name).join(" · ")));
  }
  if (value.fast) {
    calendarResult.append(element("p", "", `Fast: ${value.fast.label || value.fast.english || value.fast.level}${value.fast.note ? ` — ${value.fast.note}` : ""}`));
  }
  if (value.readings) {
    const readings = [value.readings.epistle, value.readings.gospel].filter(Boolean).join(" · ");
    if (readings) calendarResult.append(element("p", "", `Readings: ${readings}`));
  }
}

async function setupCalendar(status) {
  if (status.corpus_mode !== "plithos" || !status.calendar_available) return;
  const [module, tablesResponse] = await Promise.all([
    import("/calendar/plithos-calendar.v2.js"),
    fetch("/calendar/calendar-tables.v2.en.json"),
  ]);
  if (!tablesResponse.ok) throw new Error("calendar tables unavailable");
  const tables = await tablesResponse.json();
  calendarDay = module.calendar(tables, null, "en");
  const now = new Date();
  calendarDate.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  calendarPanel.hidden = false;
  renderCalendar();
}

calendarGo.addEventListener("click", renderCalendar);
calendarDate.addEventListener("change", renderCalendar);
calendarMode.addEventListener("change", renderCalendar);

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionNode.value.trim();
  if (!question) return;
  addUserMessage(question);
  questionNode.value = "";
  const submit = form.querySelector("button[type=submit]");
  submit.disabled = true;
  try {
    addAnswer(await request("/api/ask", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({question})}));
  } catch (error) {
    addAnswer({response_class: "error", intent: "system", text: error.message, evidence: []});
  } finally {
    submit.disabled = false;
    questionNode.focus();
  }
});

for (const button of document.querySelectorAll("[data-question]")) {
  button.addEventListener("click", () => { questionNode.value = button.dataset.question; questionNode.focus(); });
}

document.querySelector("#run-evaluation").addEventListener("click", async (event) => {
  event.currentTarget.disabled = true;
  event.currentTarget.textContent = "Running…";
  try {
    const report = await request("/api/evaluate");
    evaluationPanel.hidden = false;
    evaluationSummary.textContent = `${report.summary.passed}/${report.summary.total} passed`;
    evaluationLimit.textContent = report.claim_limit;
    evaluationResults.replaceChildren();
    for (const item of report.items) {
      const card = element("article", `eval-item ${item.passed ? "pass" : "fail"}`);
      card.append(element("strong", "", `${item.passed ? "PASS" : "FAIL"} · ${item.item_id}`));
      card.append(element("span", "", `${item.domain} · ${item.observed.response_class}`));
      evaluationResults.append(card);
    }
    evaluationPanel.scrollIntoView({behavior: "smooth", block: "start"});
  } catch (error) {
    evaluationPanel.hidden = false;
    evaluationSummary.textContent = "Evaluation failed";
    evaluationLimit.textContent = error.message;
  } finally {
    event.currentTarget.disabled = false;
    event.currentTarget.textContent = "Run behavioral evaluation";
  }
});

request("/api/status")
  .then(async (status) => {
    if (status.corpus_mode === "plithos") {
      statusNode.textContent = `Plithos ready · ${status.entity_count.toLocaleString()} entities · ${status.record_count.toLocaleString()} texts`;
      corpusDescription.textContent = "This build is using the verified local English Plithos package. Search, exact-text retrieval, calendar reckoning, citation resolution, and content-hash verification run locally; no language model is loaded yet.";
      corpusSummary.textContent = `Installed textual features: ${(status.features || []).join(", ")}. Calendar: ${status.calendar_available ? "Revised Julian + Julian" : "unavailable"}. Exact-text retrieval: ${status.supports_exact_text ? "available" : "unavailable"}.`;
      welcomeMessage.textContent = "Search for a saint, prayer, Scripture passage, glossary term, or Library text. Results below are retrieved evidence, not a synthesized AI answer.";
    } else {
      statusNode.textContent = `Demo mode · ${status.record_count} records`;
      corpusDescription.textContent = "No installed Plithos package was found, so the prototype is using its original project-policy demonstration corpus. Install the pinned corpus locally to exercise Orthodox evidence search and calendar lookup.";
      corpusSummary.textContent = "Demonstration corpus only.";
      welcomeMessage.textContent = "Demo mode is active. Install the Plithos package to search Orthodox source material and use the calendar.";
    }
    statusNode.classList.add("ready");
    showVersions(status.versions);
    try { await setupCalendar(status); } catch (error) { corpusSummary.textContent += ` Calendar error: ${error.message}.`; }
  })
  .catch((error) => { statusNode.textContent = `Prototype unavailable · ${error.message}`; });
