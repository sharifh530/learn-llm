import {api, readTab, writeTab, showXP, toast} from "./common.js";
import {ChoiceActivity} from "./activities.js";

const lesson = JSON.parse(document.querySelector("#lesson-data").textContent);
let progress = JSON.parse(document.querySelector("#progress-data").textContent);
const tabs = [...document.querySelectorAll("[data-step]")];

function selectStep(step, focus = false) {
  if (!tabs.some(tab => tab.dataset.step === step)) step = "learn";
  document.querySelector(".lesson-layout").dataset.currentStep = step;
  tabs.forEach(tab => {
    const active = tab.dataset.step === step;
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
    document.querySelector(`#panel-${tab.dataset.step}`).hidden = !active;
    if (active && focus) tab.focus();
  });
  const url = new URL(location.href);
  url.searchParams.set("step", step);
  history.replaceState(null, "", url);
}

tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => selectStep(tab.dataset.step));
  tab.addEventListener("keydown", event => {
    let next;
    if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
    if (event.key === "ArrowLeft") next = (index - 1 + tabs.length) % tabs.length;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = tabs.length - 1;
    if (next !== undefined) {event.preventDefault(); selectStep(tabs[next].dataset.step, true);}
  });
});
selectStep(new URL(location.href).searchParams.get("step") || "learn");

function updateProgress(summary, awarded = 0) {
  progress = summary;
  showXP(summary, awarded);
  const current = summary.lessons[lesson.id];
  document.querySelectorAll("[data-check]").forEach(check => {check.textContent = current[check.dataset.check] ? "✓" : "";});
  document.querySelector("#lesson-completion").hidden = !current.completed;
  document.querySelector("#lesson-status").textContent = current.completed
    ? "Lesson complete · progress saved" : "Reading + game + quiz + build practice = one complete experiment";
  document.querySelector("[data-ack=build]").textContent = current.build ? "Practice saved ✓" : "I tried the build mission";
  document.querySelector("[data-ack=reading]").textContent = current.reading ? "Reading saved · play next →" : "I read it · let’s play →";
}

for (const kind of ["game", "quiz"]) new ChoiceActivity(
  document.querySelector(`[data-activity=${kind}]`), lesson, kind, progress.lessons[lesson.id], updateProgress,
  () => selectStep(kind === "game" ? "quiz" : "build", true),
);

document.querySelectorAll("[data-ack]").forEach(button => button.addEventListener("click", async () => {
  button.disabled = true;
  try {
    const result = await api(`/api/lessons/${lesson.id}/acknowledgments`, {kind: button.dataset.ack, version: lesson.version});
    updateProgress(result.progress, result.award_added);
    if (!result.award_added) toast("Progress is already saved. Keep experimenting.");
    if (button.dataset.ack === "reading") selectStep("play", true);
  } catch (error) {toast(error.message);}
  finally {button.disabled = false;}
}));

const prediction = document.querySelector("#prediction-note");
prediction.value = readTab(`tiny-chat-prediction-${lesson.id}`);
prediction.addEventListener("input", () => writeTab(`tiny-chat-prediction-${lesson.id}`, prediction.value));
