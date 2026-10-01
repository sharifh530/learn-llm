import {api, node, readTab, writeTab} from "./common.js";

const messages = document.querySelector("#chat-messages");
const input = document.querySelector("#chat-input");
const form = document.querySelector("#chat-form");
const sendButton = document.querySelector("#chat-send");
const status = document.querySelector("#chat-status");
const greeting = "Hello, builder! I am a tiny demo made from Python rules. Ask about tokens, training, or context to see how a message travels through your app.";
let history = [];
try {
  const saved = JSON.parse(readTab("tiny-chat-demo-history", "[]"));
  if (Array.isArray(saved)) history = saved.filter(item => ["user", "assistant"].includes(item.role) && typeof item.text === "string").slice(-40);
} catch { /* Empty demo history is fine. */ }
if (!history.length) history = [{role: "assistant", text: greeting}];
input.value = readTab("tiny-chat-demo-draft");
input.addEventListener("input", () => writeTab("tiny-chat-demo-draft", input.value));

function renderMessage(message) {
  const article = node("article", `chat-message ${message.role}`);
  article.append(node("span", "message-label", message.role === "user" ? "You" : "Demo bot · Python rules"), node("p", "", message.text));
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
}
history.forEach(renderMessage);

form.addEventListener("submit", async event => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text || sendButton.disabled) return;
  sendButton.disabled = true;
  status.textContent = "Looking up a demo rule…";
  try {
    const response = await api("/api/demo/messages", {message: text});
    const userMessage = {role: "user", text};
    const botMessage = {role: "assistant", text: response.reply};
    history.push(userMessage, botMessage);
    history = history.slice(-40);
    renderMessage(userMessage);
    renderMessage(botMessage);
    writeTab("tiny-chat-demo-history", JSON.stringify(history));
    input.value = "";
    writeTab("tiny-chat-demo-draft", "");
    status.textContent = "Demo reply received · zero Google calls";
  } catch (error) {status.textContent = error.message;}
  finally {sendButton.disabled = false; input.focus({preventScroll: true});}
});

input.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {event.preventDefault(); form.requestSubmit();}
});
document.querySelectorAll("[data-chat-prompt]").forEach(button => button.addEventListener("click", () => {
  input.value = button.dataset.chatPrompt;
  writeTab("tiny-chat-demo-draft", input.value);
  form.requestSubmit();
}));
document.querySelector("#clear-chat").addEventListener("click", () => {
  history = [{role: "assistant", text: greeting}];
  writeTab("tiny-chat-demo-history", JSON.stringify(history));
  messages.replaceChildren();
  history.forEach(renderMessage);
  status.textContent = "Fresh demo conversation. Your lesson progress is unchanged.";
  input.focus();
});
