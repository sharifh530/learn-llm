export async function api(path, body) {
  let response;
  try {
    response = await fetch(path, {method: body === undefined ? "GET" : "POST", headers: {"Content-Type": "application/json"}, ...(body === undefined ? {} : {body: JSON.stringify(body)})});
  } catch {
    throw new Error("The local app could not be reached. Your input is still here; check that the Python server is running, then retry.");
  }
  const data = await response.json();
  if (!response.ok) {
    const detail = Array.isArray(data.detail) ? data.detail.map(item => item.msg).join(" ") : data.detail;
    throw new Error(detail || "That action could not be saved. Please retry.");
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
  if (amount > 0) toast(`+${amount} XP · Progress saved`);
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

const dialog = document.querySelector("#tutor-dialog");
document.querySelectorAll("[data-open-tutor]").forEach(button => button.addEventListener("click", () => dialog.showModal()));
document.querySelector("[data-close-tutor]")?.addEventListener("click", () => dialog.close());
dialog?.addEventListener("click", event => {if (event.target === dialog && event.offsetX < 0) dialog.close();});
const tutorDraft = document.querySelector("#tutor-draft");
if (tutorDraft) {
  tutorDraft.value = readTab("tiny-chat-tutor-draft");
  tutorDraft.addEventListener("input", () => writeTab("tiny-chat-tutor-draft", tutorDraft.value));
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
