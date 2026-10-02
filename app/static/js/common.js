export async function api(path, body) {
  let response;
  try {
    response = await fetch(path, {method: body === undefined ? "GET" : "POST", headers: {"Content-Type": "application/json"}, ...(body === undefined ? {} : {body: JSON.stringify(body)})});
  } catch {
    throw new Error("The app could not be reached. Your input is still here; check your connection, then retry.");
  }
  if (!response.headers.get("content-type")?.includes("application/json")) {
    throw new Error("The lab returned an unexpected response. Sign in to the hosted lab or check the server, then retry the same action.");
  }
  const data = await response.json();
  if (!response.ok) {
    const detail = Array.isArray(data.detail) ? data.detail.map(item => item.msg).join(" ") : data.detail;
    const error = new Error(detail || "That action could not be saved. Please retry.");
    error.reachedServer = true;
    error.code = data.code;
    throw error;
  }
  return data;
}

let toastTimer;
export function toast(message) {
  const element = document.querySelector("#toast");
  element.textContent = message;
  element.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {element.hidden = true;}, 4500);
}

export function showXP(progress, amount = 0) {
  document.querySelectorAll("[data-total-xp]").forEach(element => {element.textContent = progress.xp;});
  if (amount > 0) {
    toast(`+${amount} XP · Progress saved`);
    document.dispatchEvent(new CustomEvent("lab:xp", {detail: {amount}}));
  }
}

export function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

export function readTab(key, fallback = "") {
  try { return sessionStorage.getItem(key) ?? fallback; } catch { return fallback; }
}
export function writeTab(key, value) {
  try { sessionStorage.setItem(key, value); } catch { /* Draft storage is optional. */ }
}

export async function aiCall(path, body) {
  // A lost HTTP response may already have incurred a Google charge. Preserve
  // the same attempt ID across refresh/retry until the server answers.
  const key = `tiny-chat-pending-${path}-${body.lesson_id || 'chat'}`;
  const signature = JSON.stringify(body);
  let pending;
  try {pending = JSON.parse(readTab(key, "null"));} catch { /* New attempt. */ }
  if (!pending || pending.signature !== signature) pending = {signature, id: crypto.randomUUID()};
  writeTab(key, JSON.stringify(pending));
  try {
    const result = await api(path, {...body, request_id: pending.id});
    writeTab(key, "null");
    return result;
  } catch (error) {
    if (error.reachedServer && error.code !== "in_progress") writeTab(key, "null");
    throw error;
  }
}

const dialog = document.querySelector("#tutor-dialog");
document.querySelectorAll("[data-open-tutor]").forEach(button => button.addEventListener("click", () => dialog.showModal()));
document.querySelector("[data-close-tutor]")?.addEventListener("click", () => dialog.close());
dialog?.addEventListener("click", event => {if (event.target === dialog && event.offsetX < 0) dialog.close();});
const tutorDraft = document.querySelector("#tutor-draft");
if (tutorDraft) {
  const lessonData = document.querySelector("#lesson-data");
  const lesson = lessonData ? JSON.parse(lessonData.textContent) : null;
  const draftKey = `tiny-chat-tutor-draft-${lesson?.id || 'none'}`;
  tutorDraft.value = readTab(draftKey);
  tutorDraft.addEventListener("input", () => writeTab(draftKey, tutorDraft.value));
  const status = document.querySelector("#tutor-status");
  const button = document.querySelector("#tutor-send");
  button.disabled = !lesson;
  if (!lesson) status.textContent = "Open a lesson to ask a question about its content.";
  document.querySelector("#tutor-form").addEventListener("submit", async event => {
    event.preventDefault();
    if (!lesson || button.disabled) return;
    button.disabled = true;
    status.textContent = "Sending this lesson and your question to Google…";
    document.querySelector("#tutor-answer").textContent = "";
    try {
      const result = await aiCall("/api/tutor/messages", {lesson_id: lesson.id, version: lesson.version,
        mode: document.querySelector("#tutor-mode").value, message: tutorDraft.value});
      document.querySelector("#tutor-answer").textContent = result.reply;
      status.textContent = `Google AI · ${result.usage.total_tokens ?? 'unknown'} reported tokens · No XP awarded${result.truncated ? ' · Output limit reached; answer may be incomplete' : ''}`;
    } catch (error) {status.textContent = error.message;}
    finally {button.disabled = false;}
  });
}

document.querySelectorAll("[data-copy]").forEach(button => button.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(document.getElementById(button.dataset.copy).textContent);
    toast("Python copied. Paste it into a local .py file.");
  } catch {
    toast("Clipboard access is unavailable. Select the code and copy it manually.");
  }
}));

document.querySelectorAll("[data-journal]").forEach(form => {
  const key = `tiny-chat-journal-${form.dataset.lesson || "workshop"}`;
  const fields = ["changed", "learned", "confusing"];
  let saved = {};
  try {saved = JSON.parse(readTab(key, "{}"));} catch { /* Start a fresh draft. */ }
  fields.forEach(name => {form.elements[name].value = typeof saved[name] === "string" ? saved[name] : "";});
  form.addEventListener("input", () => writeTab(key, JSON.stringify(Object.fromEntries(fields.map(name => [name, form.elements[name].value])))));
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const button = form.querySelector("button[type=submit]");
    const status = form.querySelector(".form-status");
    button.disabled = true;
    status.textContent = "Saving your experiment…";
    status.classList.remove("error");
    try {
      const data = Object.fromEntries(fields.map(name => [name, form.elements[name].value]));
      data.lesson_id = form.dataset.lesson || form.elements.lesson_id.value;
      const entry = await api("/api/journal", data);
      const article = node("article", "journal-entry");
      article.append(node("span", "tag neutral", `${entry.lesson_id} · Saved experiment`), node("h3", "", entry.changed), node("p", "", entry.learned));
      if (entry.confusing) article.append(node("p", "muted", `Still wondering: ${entry.confusing}`));
      document.querySelector("[data-empty-journal]")?.remove();
      document.querySelector("[data-journal-entries]").prepend(article);
      form.reset();
      writeTab(key, "{}");
      status.textContent = "Saved locally. It will be here when you return.";
      toast("Your experiment is saved.");
    } catch (error) {
      status.classList.add("error");
      status.textContent = error.message;
    } finally {button.disabled = false;}
  });
});
