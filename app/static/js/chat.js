import {api, aiCall, node, readTab, writeTab} from "./common.js";

const messages = document.querySelector("#chat-messages");
const input = document.querySelector("#chat-input");
const form = document.querySelector("#chat-form");
const sendButton = document.querySelector("#chat-send");
const status = document.querySelector("#chat-status");
const selector = document.querySelector("#chat-mode");
let mode = "demo", history = [];
const key = name => `tiny-chat-${mode}-${name}`;
const greeting = () => mode === "demo" ? "Hello, builder! I am a tiny demo made from Python rules. Ask about tokens, training, or context." : "Google mode selected. Sending a question calls Google through your Python server and may incur charges. Each message is independent in M2.";
function renderMessage(message) {
  const article = node("article", `chat-message ${message.role}`);
  article.append(node("span", "message-label", message.role === "user" ? "You" : (mode === "demo" ? "Demo bot · Python rules" : "Google AI")), node("p", "", message.text));
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
}
function loadMode() {
  mode = selector.value;
  history = [];
  try {
    const saved = JSON.parse(readTab(key("history"), "[]"));
    if (Array.isArray(saved)) history = saved.filter(item => ["user", "assistant"].includes(item.role) && typeof item.text === "string").slice(-40);
  } catch { /* Optional tab storage. */ }
  if (!history.length) history = [{role: "assistant", text: greeting()}];
  input.value = readTab(key("draft"));
  input.maxLength = mode === "demo" ? 2000 : 4000;
  messages.replaceChildren(); history.forEach(renderMessage);
  document.querySelector("#chat-heading").textContent = mode === "demo" ? "Tiny demo bot" : "Your Google chatbot";
  document.querySelector("#chat-subtitle").textContent = mode === "demo" ? "Rule-based · Ready to experiment" : "Google Cloud · Current message only";
  document.querySelector("#chat-mode-label").textContent = mode === "demo" ? "Demo: no model connected" : "Google mode · Calls may incur charges";
  document.querySelector("#chat-mode-help").textContent = mode === "demo" ? "Hand-written replies. No Google calls. It doesn’t remember earlier messages." : "Explicit Google requests. No automatic fallback to demo. Configure and test in Settings first.";
  status.textContent = "Enter to send · Shift + Enter for a new line";
}
loadMode(); selector.addEventListener("change", loadMode);
input.addEventListener("input", () => writeTab(key("draft"), input.value));
form.addEventListener("submit", async event => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text || sendButton.disabled) return;
  sendButton.disabled = true; selector.disabled = true;
  document.querySelector("#clear-chat").disabled = true;
  status.textContent = mode === "demo" ? "Looking up a demo rule…" : "Sending your message to Google…";
  try {
    const body = {message: text};
    const response = mode === "demo" ? await api("/api/demo/messages", body) : await aiCall("/api/ai/messages", body);
    const userMessage = {role: "user", text}, botMessage = {role: "assistant", text: response.reply};
    history.push(userMessage, botMessage); history = history.slice(-40);
    renderMessage(userMessage); renderMessage(botMessage);
    writeTab(key("history"), JSON.stringify(history));
    input.value = ""; writeTab(key("draft"), "");
    status.textContent = mode === "demo" ? "Demo reply received · zero Google calls" : `Google reply received · ${response.usage.total_tokens ?? 'unknown'} reported tokens · Cost unknown${response.truncated ? ' · Output limit reached; answer may be incomplete' : ''}`;
  } catch (error) {status.textContent = error.message;}
  finally {sendButton.disabled = false; selector.disabled = false; document.querySelector("#clear-chat").disabled = false; input.focus({preventScroll: true});}
});
input.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {event.preventDefault(); form.requestSubmit();}
});
document.querySelectorAll("[data-chat-prompt]").forEach(button => button.addEventListener("click", () => {
  if (sendButton.disabled) return;
  input.value = button.dataset.chatPrompt; writeTab(key("draft"), input.value); form.requestSubmit();
}));
document.querySelector("#clear-chat").addEventListener("click", () => {
  history = [{role: "assistant", text: greeting()}]; writeTab(key("history"), JSON.stringify(history));
  messages.replaceChildren(); history.forEach(renderMessage);
  status.textContent = "Fresh conversation display. Usage records and lesson progress are unchanged."; input.focus();
});
