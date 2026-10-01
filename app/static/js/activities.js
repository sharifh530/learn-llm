import {api, node} from "./common.js";

function shuffled(choices) {
  const result = [...choices];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

export class ChoiceActivity {
  constructor(container, lesson, kind, progress, onSave, onNext) {
    this.container = container;
    this.lesson = lesson;
    this.kind = kind;
    this.activity = lesson[kind];
    this.questions = this.activity.rounds || this.activity.questions;
    this.onSave = onSave;
    this.onNext = onNext;
    this.initialProgress = progress;
    this.reset();
  }

  reset() {
    this.index = 0;
    this.answers = {};
    this.results = [];
    this.checked = false;
    this.pending = null;
    this.order = this.questions.map(question => shuffled(question.choices));
    this.renderRound();
  }

  header() {
    const header = node("div", "activity-title");
    const text = node("div");
    text.append(node("span", "tag", this.kind === "game" ? "Play with the idea" : "Explain what you learned"), node("h2", "", this.activity.title || "Three small questions."));
    const passed = this.initialProgress[this.kind];
    header.append(text, node("span", "tag neutral", passed ? `Passed · best ${this.initialProgress[`${this.kind}_score`]}/3` : "20 XP · once"));
    return header;
  }

  renderRound() {
    const question = this.questions[this.index];
    const panel = this.container;
    panel.replaceChildren(this.header());
    panel.append(node("p", "activity-intro", this.activity.instructions || "Choose an answer, check the explanation, and keep going. Two of three correct passes; hints and retries are welcome."));
    const meta = node("div", "round-meta");
    meta.append(node("span", "", `Round ${this.index + 1} of ${this.questions.length}`));
    const dots = node("div", "round-dots");
    dots.setAttribute("aria-hidden", "true");
    this.questions.forEach((_, index) => dots.append(node("span", index === this.index ? "current" : index < this.index ? this.results[index] ? "correct" : "wrong" : "")));
    meta.append(dots);
    const prompt = node("h3", "question-prompt", question.prompt);
    prompt.id = `${this.kind}-prompt`;
    panel.append(meta, prompt);
    const fieldset = node("fieldset", "choice-list");
    fieldset.dataset.question = question.id;
    fieldset.setAttribute("aria-labelledby", prompt.id);
    this.order[this.index].forEach(choice => {
      const label = node("label", "choice-option");
      const input = node("input");
      input.type = "radio";
      input.name = `${this.kind}-choice`;
      input.value = choice.id;
      label.append(input, node("span", "", choice.text));
      fieldset.append(label);
    });
    panel.append(fieldset);
    this.feedback = node("div", "round-feedback");
    this.feedback.hidden = true;
    this.feedback.setAttribute("role", "status");
    panel.append(this.feedback);
    const controls = node("div", "activity-controls");
    this.checkButton = node("button", "button", "Check my answer");
    this.checkButton.type = "button";
    this.checkButton.addEventListener("click", () => this.advance());
    this.studyButton = node("button", "link-button", "Show answers and study");
    this.studyButton.type = "button";
    this.studyButton.addEventListener("click", () => this.save(true));
    controls.append(this.checkButton, this.studyButton);
    this.error = node("p", "activity-error");
    this.error.setAttribute("role", "alert");
    panel.append(controls, this.error);
  }

  advance() {
    if (this.checked) {
      if (this.index === this.questions.length - 1) this.save(false);
      else {
        this.index += 1;
        this.checked = false;
        this.renderRound();
        this.container.querySelector(".question-prompt").setAttribute("tabindex", "-1");
        this.container.querySelector(".question-prompt").focus({preventScroll: true});
      }
      return;
    }
    const selected = this.container.querySelector("input:checked");
    if (!selected) {
      this.error.textContent = "Choose one answer first. It is okay to make a guess.";
      this.container.querySelector("input").focus();
      return;
    }
    this.error.textContent = "";
    const question = this.questions[this.index];
    this.answers[question.id] = selected.value;
    const correct = selected.value === question.correct_choice_id;
    this.results[this.index] = correct;
    this.container.querySelectorAll("input").forEach(input => {
      input.disabled = true;
      if (input.value === question.correct_choice_id) input.closest("label").classList.add("correct-choice");
      else if (input.checked) input.closest("label").classList.add("wrong-choice");
    });
    this.feedback.hidden = false;
    this.feedback.className = `round-feedback ${correct ? "correct" : "wrong"}`;
    this.feedback.replaceChildren(node("h3", "", correct ? "That fits the idea." : "A useful thing to notice."), node("p", "", question.feedback[selected.value]));
    const details = node("details");
    details.append(node("summary", "", "See feedback for every choice"));
    const list = node("ul");
    question.choices.forEach(choice => list.append(node("li", "", `${choice.text}: ${question.feedback[choice.id]}`)));
    details.append(list);
    this.feedback.append(details);
    this.checked = true;
    this.checkButton.textContent = this.index === this.questions.length - 1 ? "Save my result →" : "Next round →";
  }

  async save(study) {
    if (!this.pending || this.pending.study !== study) this.pending = {
      lesson_id: this.lesson.id, version: this.lesson.version, activity_id: this.activity.id,
      answers: study ? {} : {...this.answers}, study, idempotency_key: crypto.randomUUID(),
    };
    this.checkButton.disabled = this.studyButton.disabled = true;
    this.error.textContent = "Saving your practice…";
    try {
      const result = await api("/api/attempts", this.pending);
      this.onSave(result.progress, result.award_added);
      this.initialProgress = result.progress.lessons[this.lesson.id];
      this.renderResult(result);
    } catch (error) {
      this.error.textContent = error.message;
      this.checkButton.disabled = this.studyButton.disabled = false;
    }
  }

  renderResult(result) {
    const panel = this.container;
    const title = result.studied ? "Study is part of the process." : result.passed ? "You made the idea click." : "You are finding the tricky bits.";
    const description = result.studied ? "Answers are shown below. This attempt is marked studied, with no XP. Try a fresh practice round when you are ready."
      : result.passed ? `Practice passed and saved.${result.award_added ? ` You earned ${result.award_added} XP.` : " You already earned this activity's XP; replay is always welcome."}`
      : "This attempt is saved. Review the feedback, then try again. Two correct answers will pass.";
    const summary = node("div", "activity-result");
    summary.append(node("div", "result-symbol", result.passed ? "✓" : result.studied ? "↗" : "↻"), node("h2", "", title), node("p", "result-score", result.studied ? "Studied" : `${result.score} / ${result.total}`), node("p", "", description));
    const actions = node("div", "result-actions");
    const replay = node("button", "button secondary", "Try a fresh round");
    replay.addEventListener("click", () => this.reset());
    const next = node("button", "button", this.kind === "game" ? "Try the quick quiz →" : "Open the build mission →");
    next.addEventListener("click", this.onNext);
    actions.append(replay, next);
    summary.append(actions);
    const review = node("div", "activity-review");
    this.questions.forEach(question => {
      const details = node("details");
      const correct = question.choices.find(choice => choice.id === question.correct_choice_id);
      details.append(node("summary", "", question.prompt), node("p", "", `Correct choice: ${correct.text}`));
      const list = node("ul");
      question.choices.forEach(choice => list.append(node("li", "", `${choice.text}: ${question.feedback[choice.id]}`)));
      details.append(list);
      review.append(details);
    });
    panel.replaceChildren(this.header(), summary, review);
    summary.setAttribute("tabindex", "-1");
    summary.focus({preventScroll: true});
  }
}
