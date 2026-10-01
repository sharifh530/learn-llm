"""Render the authored lesson JSON into a readable Markdown course copy."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "STARTER_LESSONS.md"


def question_lines(question: dict) -> list[str]:
    lines = [question["prompt"], ""]
    for number, choice in enumerate(question["choices"], 1):
        lines.append(f"{number}. {choice['text']}")
    correct = next(c for c in question["choices"] if c["id"] == question["correct_choice_id"])
    lines += ["", "<details>", "<summary>Reveal answer and feedback</summary>", "",
              f"Correct: **{correct['text']}**.", ""]
    for choice in question["choices"]:
        lines.append(f"- **{choice['text']}**: {question['feedback'][choice['id']]}")
    lines += ["", "</details>", ""]
    return lines


def render() -> str:
    lines = [
        "# Authored lessons: Tiny Chat Lab", "",
        "Start with L01. Predict before running code or revealing answers. The first nine examples use only Python's standard library and run locally without Google credentials. L09's build mission separately requires an actual Google connection. Later authored lessons may introduce dependencies or live model calls explicitly.", "",
        "These are complete reading activities, also available as clickable games and quizzes in the M1 web app. Try two of three questions correctly, then complete the small build mission. The app saves lesson progress and journal entries locally.", "",
        "This reading copy is generated from `content/lessons/*.json`. Edit the JSON, then run `python tools/render_lessons.py`. Some Markdown viewers show the answer panels expanded; pause before looking at them.", "",
    ]
    for path in sorted((ROOT / "content" / "lessons").glob("*.json")):
        lesson = json.loads(path.read_text(encoding="utf-8"))
        lines += [f"## {lesson['id']}: {lesson['title']}", "",
                  f"{lesson['zone']} · about {lesson['minutes']} minutes · version {lesson['version']}", "",
                  "### Your goal", ""]
        lines.extend(f"- {goal}" for goal in lesson["objectives"])
        lines += ["", "### Predict first", "", lesson["prediction"], "", "### Learn", ""]
        for paragraph in lesson["explanation"]:
            lines += [paragraph, ""]
        lines += [f"**Where the analogy stops:** {lesson['analogy_limit']}", "",
                  "### Run a tiny Python example", "", "```python", lesson["python_example"]["code"].rstrip(), "```", "",
                  "Expected output:", "", "```text", lesson["python_example"]["expected_output"].rstrip(), "```", ""]
        lines.extend(f"- {point}" for point in lesson["python_example"]["walkthrough"])
        game = lesson["game"]
        lines += ["", f"### Play: {game['title']}", "", game["instructions"], ""]
        for index, question in enumerate(game["rounds"], 1):
            lines += [f"#### Round {index}", ""] + question_lines(question)
        lines += ["### Quick quiz", "", "Try at least two of three correctly. If you reveal a solution, study it and try again later.", ""]
        for index, question in enumerate(lesson["quiz"]["questions"], 1):
            lines += [f"#### Question {index}", ""] + question_lines(question)
        build = lesson["build"]
        lines += [f"### Build mission: {build['title']}", "", build["instructions"], "",
                  "You are done when:", ""]
        lines.extend(f"- {criterion}" for criterion in build["criteria"])
        lines += ["", "<details>", "<summary>Hints</summary>", ""]
        lines.extend(f"{number}. {hint}" for number, hint in enumerate(build["hints"], 1))
        lines += ["", "</details>", "", "<details>", "<summary>Reference solution or solution notes</summary>", "",
                  "```text", build["reference_solution"], "```", "", "</details>", "",
                  "### Explain it back", "", lesson["reflection"], "",
                  "**Ask AI when connected:** Give me a hint, use a simpler example, explain this Python, or quiz me with a fresh example.", ""]
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    OUTPUT.write_text(render(), encoding="utf-8")
    print(f"Rendered {OUTPUT}")
