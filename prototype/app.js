"use strict";

const SESSION_STORAGE_KEY = "uvaha.chatSessions.v1";
const SESSION_STORAGE_VERSION = 1;
const MAX_SESSIONS = 100;
const MAX_MESSAGES_PER_SESSION = 200;
const MAX_MESSAGE_CHARS = 50000;
const MAX_EVIDENCE_ITEMS = 20;
const MAX_CONTEXT_TURNS = 6;
const MAX_CONTEXT_TURN_CHARS = 800;
const MAX_CONTEXT_SOURCES = 4;
const MAX_SEGMENT_ID_CHARS = 200;

const statusNode = document.querySelector("#status");
const versionsNode = document.querySelector("#versions");
const messagesNode = document.querySelector("#messages");
const form = document.querySelector("#ask-form");
const questionNode = document.querySelector("#question");
const submitNode = form.querySelector("button[type=submit]");
const sourceModeNode = document.querySelector("#source-mode");
const automaticModeNode = sourceModeNode.querySelector("option[value=automatic]");
const corpusSummary = document.querySelector("#corpus-summary");
const aboutCopy = document.querySelector("#about-copy");
const sessionsToggle = document.querySelector("#sessions-toggle");
const sessionsClose = document.querySelector("#sessions-close");
const sessionDrawer = document.querySelector("#session-drawer");
const sessionScrim = document.querySelector("#session-scrim");
const newSessionButton = document.querySelector("#new-session");
const sessionList = document.querySelector("#session-list");
const archivedSessionList = document.querySelector("#archived-session-list");
const archivedSessions = document.querySelector("#archived-sessions");
const archivedCount = document.querySelector("#archived-count");
const storageStatus = document.querySelector("#storage-status");

let welcomeText = "Ask anything.";
let storageAvailable = true;
let pendingRequest = null;
let thinkingTimerId = null;

function element(name, className, text) {
  const node = document.createElement(name);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function boundedString(value, limit, fallback = "") {
  return typeof value === "string" ? value.slice(0, limit) : fallback;
}

function newSessionId() {
  if (window.crypto && typeof window.crypto.randomUUID === "function") {
    return window.crypto.randomUUID();
  }
  return `chat-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

function makeSession() {
  const now = Date.now();
  return {
    id: newSessionId(),
    title: "New chat",
    createdAt: now,
    updatedAt: now,
    archived: false,
    messages: [],
  };
}

function normalizeEvidence(item) {
  if (!item || typeof item !== "object") return null;
  return {
    title: boundedString(item.title, 500, "Source"),
    display_text: boundedString(item.display_text, MAX_MESSAGE_CHARS),
    citation_label: boundedString(item.citation_label, 1000),
    source_class: boundedString(item.source_class, 100),
    source_locator: boundedString(item.source_locator, 2048),
    origin: boundedString(item.origin, 40, "local").toLowerCase(),
    segment_id: boundedString(item.segment_id, MAX_SEGMENT_ID_CHARS),
    content_sha256: boundedString(item.content_sha256, 64).toLowerCase(),
  };
}

function normalizeMessage(message) {
  if (!message || typeof message !== "object") return null;
  if (message.role !== "user" && message.role !== "assistant") return null;
  const text = boundedString(message.text, MAX_MESSAGE_CHARS);
  if (!text) return null;
  if (message.role === "user") return {role: "user", text};
  const elapsed = Number(message.elapsedSeconds);
  const evidence = Array.isArray(message.evidence)
    ? message.evidence.slice(0, MAX_EVIDENCE_ITEMS).map(normalizeEvidence).filter(Boolean)
    : [];
  return {
    role: "assistant",
    text,
    responseClass: boundedString(message.responseClass, 80, "informational"),
    elapsedSeconds: Number.isFinite(elapsed) ? Math.max(0, Math.min(elapsed, 86400)) : undefined,
    evidence,
    hadTransientWebSources: message.hadTransientWebSources === true
      || evidence.some((item) => item.origin === "web"),
  };
}

function normalizeSession(session, seenIds) {
  if (!session || typeof session !== "object") return null;
  const id = boundedString(session.id, 100);
  if (!id || seenIds.has(id)) return null;
  seenIds.add(id);
  const createdAt = Number(session.createdAt);
  const updatedAt = Number(session.updatedAt);
  return {
    id,
    title: boundedString(session.title, 80, "New chat") || "New chat",
    createdAt: Number.isFinite(createdAt) ? createdAt : Date.now(),
    updatedAt: Number.isFinite(updatedAt) ? updatedAt : Date.now(),
    archived: session.archived === true,
    messages: Array.isArray(session.messages)
      ? session.messages.slice(-MAX_MESSAGES_PER_SESSION).map(normalizeMessage).filter(Boolean)
      : [],
  };
}

function loadSessionState() {
  try {
    const saved = window.localStorage.getItem(SESSION_STORAGE_KEY);
    if (!saved) return {version: SESSION_STORAGE_VERSION, activeId: "", sessions: []};
    const parsed = JSON.parse(saved);
    if (!parsed || parsed.version !== SESSION_STORAGE_VERSION || !Array.isArray(parsed.sessions)) {
      return {version: SESSION_STORAGE_VERSION, activeId: "", sessions: []};
    }
    const seenIds = new Set();
    return {
      version: SESSION_STORAGE_VERSION,
      activeId: boundedString(parsed.activeId, 100),
      sessions: parsed.sessions.slice(0, MAX_SESSIONS).map((session) => normalizeSession(session, seenIds)).filter(Boolean),
    };
  } catch (_error) {
    storageAvailable = false;
    return {version: SESSION_STORAGE_VERSION, activeId: "", sessions: []};
  }
}

const sessionState = loadSessionState();

function getSession(sessionId) {
  return sessionState.sessions.find((session) => session.id === sessionId) || null;
}

function getActiveSession() {
  return getSession(sessionState.activeId);
}

function ensureActiveSession() {
  let active = getActiveSession();
  if (!active || active.archived) {
    active = sessionState.sessions
      .filter((session) => !session.archived)
      .sort((left, right) => right.updatedAt - left.updatedAt)[0];
  }
  if (!active) {
    active = makeSession();
    sessionState.sessions.unshift(active);
  }
  sessionState.activeId = active.id;
  return active;
}

function saveSessionState() {
  if (!storageAvailable) {
    storageStatus.textContent = "Chats will last until this page is closed.";
    return;
  }
  try {
    const persisted = {
      version: SESSION_STORAGE_VERSION,
      activeId: sessionState.activeId,
      sessions: sessionState.sessions.map((session) => ({
        id: session.id,
        title: session.title,
        createdAt: session.createdAt,
        updatedAt: session.updatedAt,
        archived: session.archived,
        messages: session.messages.map((message) => message.role === "user" ? {
          role: "user",
          text: message.text,
        } : {
          role: "assistant",
          text: message.text,
          responseClass: message.responseClass,
          elapsedSeconds: message.elapsedSeconds,
          hadTransientWebSources: message.hadTransientWebSources === true,
          evidence: (message.evidence || []).filter((item) => item.origin !== "web"),
        }),
      })),
    };
    window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(persisted));
    storageStatus.textContent = "Saved only in this browser.";
  } catch (_error) {
    storageAvailable = false;
    storageStatus.textContent = "Chats will last until this page is closed.";
  }
}

function titleFromQuestion(question) {
  const title = question.replace(/\s+/g, " ").trim();
  return title.length > 52 ? `${title.slice(0, 51).trimEnd()}…` : title;
}

function formatSessionTime(timestamp) {
  try {
    return new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(new Date(timestamp));
  } catch (_error) {
    return "Saved chat";
  }
}

function sessionItem(session, isArchived) {
  const item = element("li", `session-item${session.id === sessionState.activeId ? " current" : ""}`);
  const heading = element("div", "session-item-heading");
  if (isArchived) {
    heading.append(element("span", "session-title", session.title));
  } else {
    const select = element("button", "session-title", session.title);
    select.type = "button";
    select.dataset.action = "select";
    select.dataset.sessionId = session.id;
    if (session.id === sessionState.activeId) select.setAttribute("aria-current", "page");
    heading.append(select);
  }
  const isPending = pendingRequest && pendingRequest.sessionId === session.id;
  heading.append(element("span", "session-time", isPending ? "Answering…" : formatSessionTime(session.updatedAt)));
  item.append(heading);

  const actions = element("div", "session-actions");
  const primaryAction = element("button", "session-action", isArchived ? "Restore" : "Archive");
  primaryAction.type = "button";
  primaryAction.dataset.action = isArchived ? "restore" : "archive";
  primaryAction.dataset.sessionId = session.id;
  primaryAction.disabled = Boolean(isPending);
  primaryAction.setAttribute("aria-label", `${isArchived ? "Restore" : "Archive"} ${session.title}`);
  actions.append(primaryAction);
  const remove = element("button", "session-action danger", "Delete");
  remove.type = "button";
  remove.dataset.action = "delete";
  remove.dataset.sessionId = session.id;
  remove.disabled = Boolean(isPending);
  remove.setAttribute("aria-label", `Delete ${session.title}`);
  actions.append(remove);
  item.append(actions);
  return item;
}

function renderSessionLists() {
  const byRecent = (left, right) => right.updatedAt - left.updatedAt;
  const current = sessionState.sessions.filter((session) => !session.archived).sort(byRecent);
  const archived = sessionState.sessions.filter((session) => session.archived).sort(byRecent);
  sessionList.replaceChildren(...current.map((session) => sessionItem(session, false)));
  archivedSessionList.replaceChildren(...archived.map((session) => sessionItem(session, true)));
  archivedCount.textContent = String(archived.length);
  archivedSessions.hidden = archived.length === 0;
}

function openSessionDrawer() {
  sessionDrawer.hidden = false;
  sessionScrim.hidden = false;
  sessionsToggle.setAttribute("aria-expanded", "true");
  document.body.classList.add("drawer-open");
  window.requestAnimationFrame(() => sessionsClose.focus());
}

function closeSessionDrawer(returnFocus = true) {
  sessionDrawer.hidden = true;
  sessionScrim.hidden = true;
  sessionsToggle.setAttribute("aria-expanded", "false");
  document.body.classList.remove("drawer-open");
  if (returnFocus) sessionsToggle.focus();
}

function createSession() {
  if (sessionState.sessions.length >= MAX_SESSIONS) {
    storageStatus.textContent = "Delete a chat before creating another.";
    openSessionDrawer();
    return;
  }
  const session = makeSession();
  sessionState.sessions.unshift(session);
  sessionState.activeId = session.id;
  saveSessionState();
  renderApplication();
  closeSessionDrawer(false);
  questionNode.focus();
}

function selectSession(sessionId) {
  const session = getSession(sessionId);
  if (!session || session.archived) return;
  sessionState.activeId = session.id;
  saveSessionState();
  renderApplication();
  closeSessionDrawer(false);
  questionNode.focus();
}

function archiveSession(sessionId) {
  const session = getSession(sessionId);
  if (!session || session.archived || (pendingRequest && pendingRequest.sessionId === sessionId)) return;
  session.archived = true;
  session.updatedAt = Date.now();
  if (sessionState.activeId === sessionId) {
    sessionState.activeId = "";
    ensureActiveSession();
  }
  saveSessionState();
  renderApplication();
}

function restoreSession(sessionId) {
  const session = getSession(sessionId);
  if (!session || !session.archived) return;
  session.archived = false;
  session.updatedAt = Date.now();
  sessionState.activeId = session.id;
  saveSessionState();
  renderApplication();
  closeSessionDrawer(false);
  questionNode.focus();
}

function deleteSession(sessionId) {
  const session = getSession(sessionId);
  if (!session || (pendingRequest && pendingRequest.sessionId === sessionId)) return;
  const confirmed = window.confirm(`Delete "${session.title}" and all of its messages from this browser? This cannot be undone.`);
  if (!confirmed) return;
  sessionState.sessions = sessionState.sessions.filter((candidate) => candidate.id !== sessionId);
  if (sessionState.activeId === sessionId) sessionState.activeId = "";
  ensureActiveSession();
  saveSessionState();
  renderApplication();
}

function handleSessionAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const sessionId = button.dataset.sessionId;
  if (button.dataset.action === "select") selectSession(sessionId);
  if (button.dataset.action === "archive") archiveSession(sessionId);
  if (button.dataset.action === "restore") restoreSession(sessionId);
  if (button.dataset.action === "delete") deleteSession(sessionId);
}

async function request(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `Request failed: ${response.status}`);
  return payload;
}

function showVersions(versions) {
  versionsNode.replaceChildren();
  for (const [name, value] of Object.entries(versions || {})) {
    versionsNode.append(element("dt", "", name.replaceAll("_", " ")));
    versionsNode.append(element("dd", "", value));
  }
}

function userMessage(message) {
  const article = element("article", "message user");
  article.append(element("p", "", message.text));
  return article;
}

function formatElapsed(seconds) {
  const whole = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(whole / 60);
  const remainder = whole % 60;
  return minutes ? `${minutes}m ${String(remainder).padStart(2, "0")}s` : `${remainder}s`;
}

function thinkingMessage(started) {
  const article = element("article", "message assistant thinking");
  article.setAttribute("role", "status");
  const timer = element("p", "elapsed thinking-elapsed", `Thinking · ${formatElapsed((performance.now() - started) / 1000)}`);
  article.append(timer);
  return article;
}

function updateThinkingTimer() {
  if (!pendingRequest || sessionState.activeId !== pendingRequest.sessionId) return;
  const timer = messagesNode.querySelector(".thinking-elapsed");
  if (timer) timer.textContent = `Thinking · ${formatElapsed((performance.now() - pendingRequest.started) / 1000)}`;
}

function safeHttpsLink(value) {
  if (typeof value !== "string") return null;
  try {
    const url = new URL(value);
    if (url.protocol !== "https:") return null;
    const link = element("a", "source-link", url.hostname);
    link.href = url.href;
    link.target = "_blank";
    link.rel = "noreferrer noopener";
    return link;
  } catch (_error) {
    return null;
  }
}

function addSources(evidence) {
  if (!evidence.length) return null;
  const details = element("details", "sources");
  details.append(element("summary", "", `Sources (${evidence.length})`));
  const list = element("ol", "source-list");
  evidence.forEach((item) => {
    const card = element("li", "source-card");
    card.append(element("strong", "", item.title || "Source"));
    if (item.display_text) card.append(element("blockquote", "", item.display_text));
    const footer = element("p", "source-meta", item.citation_label || item.source_class || "Source");
    const link = safeHttpsLink(item.source_locator);
    if (link) footer.append(" · ", link);
    card.append(footer);
    list.append(card);
  });
  details.append(list);
  return details;
}

function assistantMessage(message) {
  const className = message.responseClass === "error" ? "message assistant error" : "message assistant";
  const article = element("article", className);
  article.append(element("p", "", message.text));
  if (message.elapsedSeconds !== undefined) article.append(element("p", "elapsed", formatElapsed(message.elapsedSeconds)));
  const sources = addSources(message.evidence || []);
  if (sources) article.append(sources);
  const hasVisibleWebSource = (message.evidence || []).some((item) => item.origin === "web");
  if (message.hadTransientWebSources && !hasVisibleWebSource) {
    article.append(element("p", "transient-source-note", "Web sources for this saved answer were not stored."));
  }
  return article;
}

function renderConversation() {
  const session = ensureActiveSession();
  messagesNode.replaceChildren();
  if (session.messages.length === 0) {
    const welcome = element("article", "message assistant welcome");
    welcome.append(element("p", "", welcomeText));
    messagesNode.append(welcome);
  } else {
    for (const message of session.messages) {
      messagesNode.append(message.role === "user" ? userMessage(message) : assistantMessage(message));
    }
  }
  if (pendingRequest && pendingRequest.sessionId === session.id) {
    messagesNode.append(thinkingMessage(pendingRequest.started));
  }
  messagesNode.scrollTop = messagesNode.scrollHeight;
}

function renderApplication() {
  renderSessionLists();
  renderConversation();
}

function storedAnswer(answer, elapsedSeconds) {
  const answerText = typeof answer.text === "string" && answer.text
    ? answer.text
    : "No answer was returned.";
  return normalizeMessage({
    role: "assistant",
    text: answerText,
    responseClass: answer.response_class,
    elapsedSeconds,
    evidence: answer.evidence,
  });
}

function localConversationHistory(messages) {
  return messages
    .slice(-MAX_CONTEXT_TURNS)
    .filter((message) => message.role === "user"
      || (message.role === "assistant" && message.hadTransientWebSources !== true))
    .map((message) => ({
      role: message.role,
      content: boundedString(message.text, MAX_CONTEXT_TURN_CHARS),
    }))
    .filter((turn) => turn.content.trim());
}

function localContextSources(messages) {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index];
    if (message.role !== "assistant") continue;
    if (message.hadTransientWebSources === true) return [];
    return (message.evidence || [])
      .filter((item) => item.origin !== "web"
        && item.segment_id
        && /^[0-9a-f]{64}$/.test(item.content_sha256 || ""))
      .slice(0, MAX_CONTEXT_SOURCES)
      .map((item) => ({
        segment_id: item.segment_id,
        content_sha256: item.content_sha256,
      }));
  }
  return [];
}

function setInteractionBusy(isBusy) {
  submitNode.disabled = isBusy;
  questionNode.disabled = isBusy;
  sourceModeNode.disabled = isBusy;
}

function setSourceAvailability(status) {
  const webAvailable = status.web_available === true;
  automaticModeNode.disabled = !webAvailable;
  if (!webAvailable) sourceModeNode.value = "local_only";
  sourceModeNode.title = webAvailable ? "Use local and web sources when helpful" : "Web sources are not available";
  return webAvailable;
}

function describeStatus(status, webAvailable) {
  if (status.generative_model_loaded) {
    statusNode.textContent = webAvailable ? "Ready · local + web sources" : "Ready · local sources";
  } else {
    statusNode.textContent = webAvailable ? "Search ready · local + web sources" : "Search ready · local sources";
  }
  statusNode.classList.add("ready");
}

// Enter sends, shift with it makes a new line. Every assistant a reader has
// used works that way, and a composer that needs the mouse to send makes the
// application feel like a form rather than a conversation.
questionNode.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" || event.shiftKey || event.ctrlKey || event.metaKey || event.altKey) return;
  if (event.isComposing) return;   // mid-composition in an IME, not a send
  event.preventDefault();
  if (typeof form.requestSubmit === "function") form.requestSubmit();
  else form.dispatchEvent(new Event("submit", {cancelable: true}));
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (pendingRequest) return;
  const question = questionNode.value.trim();
  if (!question) return;
  const session = ensureActiveSession();
  const sourceMode = sourceModeNode.value;
  const history = localConversationHistory(session.messages);
  const contextSources = localContextSources(session.messages);
  session.messages.push({role: "user", text: question});
  session.messages = session.messages.slice(-MAX_MESSAGES_PER_SESSION);
  if (session.title === "New chat") session.title = titleFromQuestion(question);
  session.updatedAt = Date.now();
  questionNode.value = "";
  pendingRequest = {sessionId: session.id, started: performance.now()};
  saveSessionState();
  setInteractionBusy(true);
  renderApplication();
  thinkingTimerId = window.setInterval(updateThinkingTimer, 1000);
  try {
    const answer = await request("/api/ask", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        question,
        source_mode: sourceMode,
        history,
        context_sources: contextSources,
      }),
    });
    const target = getSession(session.id);
    if (target) {
      target.messages.push(storedAnswer(answer, (performance.now() - pendingRequest.started) / 1000));
      target.messages = target.messages.slice(-MAX_MESSAGES_PER_SESSION);
      target.updatedAt = Date.now();
      saveSessionState();
    }
  } catch (error) {
    const target = getSession(session.id);
    if (target) {
      target.messages.push(storedAnswer({response_class: "error", text: error.message, evidence: []}, (performance.now() - pendingRequest.started) / 1000));
      target.messages = target.messages.slice(-MAX_MESSAGES_PER_SESSION);
      target.updatedAt = Date.now();
      saveSessionState();
    }
  } finally {
    window.clearInterval(thinkingTimerId);
    thinkingTimerId = null;
    pendingRequest = null;
    setInteractionBusy(false);
    renderApplication();
    questionNode.focus();
  }
});

sessionsToggle.addEventListener("click", openSessionDrawer);
sessionsClose.addEventListener("click", () => closeSessionDrawer());
sessionScrim.addEventListener("click", () => closeSessionDrawer());
newSessionButton.addEventListener("click", createSession);
sessionList.addEventListener("click", handleSessionAction);
archivedSessionList.addEventListener("click", handleSessionAction);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !sessionDrawer.hidden) closeSessionDrawer();
});


ensureActiveSession();
saveSessionState();
renderApplication();

request("/api/status")
  .then((status) => {
    const webAvailable = setSourceAvailability(status);
    describeStatus(status, webAvailable);
    welcomeText = webAvailable
      ? "Ask anything. Choose Automatic when you want Uvaha to search the web."
      : "Ask anything. Uvaha will use your local library.";
    aboutCopy.textContent = webAvailable
      ? "Uvaha answers with sources you can inspect. In Automatic mode, your search terms may be sent to Brave Search; answer generation remains on this device."
      : "Uvaha answers with sources you can inspect from your local library.";
    corpusSummary.textContent = status.corpus_mode === "plithos"
      ? `${status.entity_count.toLocaleString()} local entries · ${webAvailable ? "web available" : "local only"}`
      : `${status.record_count} local entries · ${webAvailable ? "web available" : "local only"}`;
    showVersions(status.versions);
    renderConversation();
  })
  .catch((error) => {
    statusNode.textContent = "Unavailable";
    statusNode.title = error.message;
  });
