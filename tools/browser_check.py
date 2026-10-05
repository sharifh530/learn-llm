"""Exercise the offline learning flow in Chromium with an isolated database."""

from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen
from uuid import uuid4

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]


def run():
    run_dir = (ROOT / "data" / "browser-checks" / uuid4().hex).resolve()
    assert run_dir.is_relative_to(ROOT.resolve())
    run_dir.mkdir(parents=True)
    screenshots = ROOT / "data" / "qa"
    screenshots.mkdir(parents=True, exist_ok=True)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    environment = {**os.environ, "TINY_CHAT_DATABASE": str(run_dir / "browser-test.db"), "AI_ENABLED": "false"}
    with (run_dir / "server.log").open("w", encoding="utf-8") as log:
        server = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:create_app", "--factory", "--host", "127.0.0.1", "--port", str(port)],
                                  cwd=ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT)
        try:
            for _ in range(80):
                try:
                    with urlopen(base + "/health", timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("Isolated test server did not start.")
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                context = browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
                page = context.new_page()
                errors, external = [], []
                page.on("pageerror", lambda error: errors.append(str(error)))
                def route_request(route):
                    if route.request.url.startswith(base):
                        route.continue_()
                    else:
                        external.append(route.request.url)
                        route.abort()
                context.route("**/*", route_request)

                def goto(path):
                    response = page.goto(base + path)
                    assert response.status == 200, path

                def progress():
                    return context.request.get(base + "/api/progress").json()

                def exercise(lesson, kind, wrong_first=False):
                    page.locator(f"[data-step={'play' if kind == 'game' else 'quiz'}]").click()
                    panel = page.locator(f"[data-activity={kind}]")
                    questions = lesson[kind].get("rounds", lesson[kind].get("questions"))
                    for index, question in enumerate(questions):
                        chosen = question["correct_choice_id"]
                        if wrong_first and index == 0:
                            chosen = next(option["id"] for option in question["choices"] if option["id"] != chosen)
                        panel.locator(f"input[value='{chosen}']").check()
                        panel.get_by_role("button", name="Check my answer", exact=True).click()
                        expect(panel.locator(".round-feedback")).to_be_visible()
                        if index < 2:
                            panel.get_by_role("button", name="Next round", exact=False).click()
                        else:
                            panel.get_by_role("button", name="Save my result", exact=False).click()
                    expect(panel.locator(".activity-result")).to_contain_text("Practice passed and saved.")

                goto("/")
                page.screenshot(path=str(screenshots / "home-desktop.png"), full_page=True)
                page.get_by_role("button", name="socks", exact=True).click()
                expect(page.locator("#preview-feedback")).to_contain_text("silly story")
                page.get_by_role("button", name="tea", exact=True).click()
                expect(page.locator("#preview-feedback")).to_contain_text("not a fact check")
                page.get_by_role("link", name="Start your first experiment").click()
                page.locator("[data-activity=game] .choice-list").wait_for(state="attached")
                expect(page.locator("[data-step=learn]")).to_have_attribute("aria-selected", "true")
                page.locator("[data-step=learn]").focus()
                page.keyboard.press("ArrowRight")
                expect(page.locator("[data-step=play]")).to_have_attribute("aria-selected", "true")
                page.keyboard.press("ArrowLeft")
                page.locator("[data-open-tutor]").click()
                expect(page.locator("#tutor-dialog")).to_be_visible()
                page.locator("#tutor-draft").fill("Why isn't saving a chat training?")
                page.keyboard.press("Escape")
                expect(page.locator("[data-open-tutor]")).to_be_focused()
                page.locator("[data-open-tutor]").click()
                expect(page.locator("#tutor-draft")).to_have_value("Why isn't saving a chat training?")
                page.locator("#tutor-send").click()
                expect(page.locator("#tutor-status")).to_contain_text("AI is disabled")
                expect(page.locator("#tutor-draft")).to_have_value("Why isn't saving a chat training?")
                page.locator("[data-close-tutor]").click()
                page.locator("[data-ack=reading]").click()
                expect(page.locator("[data-total-xp]")).to_have_text("10")
                page.screenshot(path=str(screenshots / "lesson-play-desktop.png"), full_page=True)
                for number in range(1, 19):
                    identity = f"L{number:02}"
                    lesson = context.request.get(base + f"/api/lessons/{identity}").json()
                    if number > 1:
                        goto(f"/lessons/{identity}")
                        page.locator("[data-ack=reading]").click()
                        expect(page.locator("[data-step=play]")).to_have_attribute("aria-selected", "true")
                    if number == 2:
                        panel = page.locator("[data-activity=game]")
                        before = progress()["xp"]
                        panel.get_by_role("button", name="Show answers and study").click()
                        expect(panel.locator(".activity-result")).to_contain_text("marked studied, with no XP")
                        assert progress()["xp"] == before
                        panel.get_by_role("button", name="Try a fresh round").click()
                    exercise(lesson, "game", wrong_first=number == 1)
                    exercise(lesson, "quiz")
                    page.locator("[data-step=build]").click()
                    page.locator("[data-ack=build]").click()
                    expect(page.locator("#lesson-completion")).to_be_visible()
                assert progress()["xp"] == 1440 and progress()["completed"] == 18
                assert len(progress()["badges"]) == 2
                goto("/lessons/L01?step=play")
                lesson = context.request.get(base + "/api/lessons/L01").json()
                exercise(lesson, "game")
                assert progress()["xp"] == 1440
                page.locator("[data-step=build]").click()
                form = page.locator("[data-journal]")
                form.locator("[name=changed]").fill("Added a robot prediction")
                form.locator("[name=learned]").fill("A dictionary lookup has an honest fallback")
                form.get_by_role("button", name="Save my experiment").click()
                expect(page.locator("[data-journal-entries]")).to_contain_text("Added a robot prediction")
                page.reload()
                expect(page.locator("[data-journal-entries]")).to_contain_text("Added a robot prediction")
                assert progress()["journal_count"] == 1
                goto("/chat")
                expect(page.locator(".chat-aside .notice")).to_contain_text("Demo: no model connected")
                page.get_by_role("button", name="What is a token?", exact=True).click()
                expect(page.locator(".chat-message").last).to_contain_text("A token is a piece of text")
                expect(page.locator('#chat-status')).to_contain_text('Demo reply received')
                page.locator("#chat-input").fill("<script>window.injected=true</script>")
                page.locator("#chat-send").click()
                expect(page.locator(".chat-message").last).to_contain_text("I do not have a rule")
                expect(page.locator('#chat-status')).to_contain_text('Demo reply received')
                assert page.evaluate("window.injected === undefined")
                page.reload()
                expect(page.locator("#chat-messages")).to_contain_text("<script>window.injected=true</script>")
                page.locator("#chat-mode").select_option("google_cloud")
                page.locator("#chat-input").fill("Keep this question on failure")
                page.locator("#chat-send").click()
                expect(page.locator("#chat-status")).to_contain_text("AI is disabled")
                expect(page.locator("#chat-input")).to_have_value("Keep this question on failure")
                expect(page.locator("#chat-messages")).not_to_contain_text("<script>window.injected=true</script>")
                page.locator("#chat-mode").select_option("demo")
                expect(page.locator("#chat-messages")).to_contain_text("<script>window.injected=true</script>")
                page.screenshot(path=str(screenshots / "chat-desktop.png"), full_page=True)
                goto("/settings")
                page.locator("#reload-content").click()
                expect(page.locator("#reload-status")).to_contain_text("18 lessons reloaded")
                page.locator("#test-provider").click()
                expect(page.locator("#provider-test-status")).to_contain_text("AI is disabled")
                assert progress()["xp"] == 1440
                goto("/lessons/L19")
                expect(page.locator(".unavailable")).to_contain_text("Coming in a later session")

                for width in (390, 640, 1280):
                    page.set_viewport_size({"width": width, "height": 850})
                    for path in ("/", "/lessons/L01", "/lessons/L05?step=play", "/workshop", "/chat", "/settings"):
                        goto(path)
                        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), f"Horizontal overflow: {width}px {path}"
                        if width == 390 and path in ("/", "/lessons/L05?step=play", "/chat"):
                            name = {"/": "home-mobile.png", "/lessons/L05?step=play": "lesson-mobile.png", "/chat": "chat-mobile.png"}[path]
                            page.screenshot(path=str(screenshots / name), full_page=True)
                assert not errors, errors
                assert not external, external
                report = {"status": "passed", "browser": "Chromium", "game_quiz_rounds": 108,
                          "completed_lessons": 18, "xp": 1440, "checks": ["wrong-answer feedback", "study mode", "replay", "journal reload", "keyboard tabs", "dialog focus", "safe demo output", "content reload", "outline availability", "disabled AI preserves questions", "demo and AI display isolation"],
                          "viewport_widths": [390, 640, 1280, 1440], "reduced_motion": True,
                          "external_requests": external, "javascript_errors": errors,
                          "database": "isolated test database; learner progress untouched"}
                (screenshots / "browser-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
                print(json.dumps(report, indent=2))
                browser.close()
        finally:
            server.terminate()
            server.wait(timeout=10)


if __name__ == "__main__":
    run()
