"use strict";

const statusNode = document.querySelector("#status");
const versionsNode = document.querySelector("#versions");
const messagesNode = document.querySelector("#messages");
const form = document.querySelector("#ask-form");
const questionNode = document.querySelector("#question");
const evaluationPanel = document.querySelector("#evaluation-panel");
const evaluationSummary = document.querySelector("#evaluation-summary");
const evaluationLimit = document.querySelector("#evaluation-limit");
const evaluationResults = document.querySelector("#evaluation-results");

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
    card.append(element("blockquote", "", evidence.display_text));
    card.append(element("cite", "", `${evidence.citation_label} · ${evidence.segment_id}`));
    article.append(card);
  }
  messagesNode.append(article);
  messagesNode.scrollTop = messagesNode.scrollHeight;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionNode.value.trim();
  if (!question) return;
  addUserMessage(question);
  questionNode.value = "";
  const submit = form.querySelector("button[type=submit]");
  submit.disabled = true;
  try {
    const answer = await request("/api/ask", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({question}),
    });
    addAnswer(answer);
  } catch (error) {
    addAnswer({response_class: "error", intent: "system", text: error.message, evidence: []});
  } finally {
    submit.disabled = false;
    questionNode.focus();
  }
});

for (const button of document.querySelectorAll("[data-question]")) {
  button.addEventListener("click", () => {
    questionNode.value = button.dataset.question;
    questionNode.focus();
  });
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
  .then((status) => {
    statusNode.textContent = `Offline core ready · ${status.record_count} demo records`;
    statusNode.classList.add("ready");
    showVersions(status.versions);
  })
  .catch((error) => {
    statusNode.textContent = `Prototype unavailable · ${error.message}`;
  });

