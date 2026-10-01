from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.content import ContentError, ContentStore
from app.main import create_app
from app.config import AISettings


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def setup(tmp_path):
    content = tmp_path / "content"
    shutil.copytree(ROOT / "content", content)
    database = tmp_path / "progress.db"
    application = create_app(database, content, ai_settings=AISettings())
    with TestClient(application) as client:
        yield client, application, database, content


def answers(lesson, kind, correct=True):
    activity = lesson[kind]
    questions = activity.get("rounds", activity.get("questions"))
    return {question["id"]: question["correct_choice_id"] if correct else next(
        choice["id"] for choice in question["choices"] if choice["id"] != question["correct_choice_id"]
    ) for question in questions}


def attempt_body(lesson, kind, correct=True, **extra):
    return {"lesson_id": lesson["id"], "version": lesson["version"], "activity_id": lesson[kind]["id"],
            "answers": answers(lesson, kind, correct), "idempotency_key": str(uuid4()), **extra}


def complete(client, identity="L01"):
    lesson = client.get(f"/api/lessons/{identity}").json()
    for kind in ("reading", "build"):
        assert client.post(f"/api/lessons/{identity}/acknowledgments", json={"kind": kind, "version": lesson["version"]}).status_code == 200
    for kind in ("game", "quiz"):
        assert client.post("/api/attempts", json=attempt_body(lesson, kind)).json()["passed"]
    return lesson


def test_pages_and_availability(setup):
    client, *_ = setup
    for path in ("/", "/workshop", "/chat", "/settings", *(f"/lessons/L{i:02}" for i in range(1, 13))):
        response = client.get(path)
        assert response.status_code == 200, path
        assert "Tiny Chat" in response.text
    assert "Coming in a later session" in client.get("/lessons/L13").text
    assert client.get("/api/lessons/L13").status_code == 404
    assert len(client.get("/api/course").json()["lessons"]) == 24


@pytest.mark.parametrize("identity", [f"L{i:02}" for i in range(1, 13)])
def test_all_lessons_score_choices_and_feedback(setup, identity):
    client, *_ = setup
    lesson = client.get(f"/api/lessons/{identity}").json()
    for kind in ("game", "quiz"):
        bad = client.post("/api/attempts", json=attempt_body(lesson, kind, correct=False)).json()
        assert bad["score"] == 0 and not bad["passed"] and bad["award_added"] == 0
        good = client.post("/api/attempts", json=attempt_body(lesson, kind)).json()
        assert good["score"] == 3 and good["passed"] and good["award_added"] == 20
        assert len(good["feedback"]) == 3
        assert all(len(round["feedback"]) == 3 for round in good["feedback"])


def test_completion_restart_journal_and_replay(setup):
    client, _, database, content = setup
    lesson = complete(client)
    body = attempt_body(lesson, "game")
    assert client.post("/api/attempts", json=body).json()["award_added"] == 0
    replay = client.post("/api/attempts", json=body).json()
    assert replay["replayed"] and replay["award_added"] == 0
    journal = {"lesson_id": "L01", "changed": "Added a robot prefix", "learned": "get uses a fallback", "confusing": ""}
    assert client.post("/api/journal", json=journal).status_code == 200
    with TestClient(create_app(database, content)) as restarted:
        saved = restarted.get("/api/progress").json()
        assert saved["xp"] == 80 and saved["lessons"]["L01"]["completed"]
        assert saved["continue_id"] == "L02"
        assert restarted.get("/api/journal").json()[0]["changed"] == journal["changed"]


def test_concurrent_retry_is_once_only(setup):
    client, app, *_ = setup
    lesson = client.get("/api/lessons/L01").json()
    body = attempt_body(lesson, "game")
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: client.post("/api/attempts", json=body), range(4)))
    assert all(result.status_code == 200 for result in results)
    assert sum(result.json()["award_added"] for result in results) == 20
    assert app.state.progress.summary()["xp"] == 20


def test_study_is_not_pass_and_does_not_remove_earned_progress(setup):
    client, *_ = setup
    lesson = client.get("/api/lessons/L01").json()
    body = attempt_body(lesson, "game", study=True, answers={})
    studied = client.post("/api/attempts", json=body).json()
    assert studied["studied"] and not studied["passed"] and studied["award_added"] == 0
    assert studied["progress"]["lessons"]["L01"]["game_studied"]
    client.post("/api/attempts", json=attempt_body(lesson, "game"))
    body["idempotency_key"] = str(uuid4())
    again = client.post("/api/attempts", json=body).json()
    assert again["progress"]["lessons"]["L01"]["game"]
    assert again["progress"]["xp"] == 20


def test_invalid_answers_versions_and_conflicting_retries(setup):
    client, *_ = setup
    lesson = client.get("/api/lessons/L01").json()
    body = attempt_body(lesson, "game")
    invalid = {**body, "answers": {}}
    assert client.post("/api/attempts", json=invalid).status_code == 400
    invalid = {**body, "version": 99}
    assert client.post("/api/attempts", json=invalid).status_code == 409
    invalid = {**body, "score": 999}
    assert client.post("/api/attempts", json=invalid).status_code == 422
    assert client.post("/api/attempts", json=body).status_code == 200
    invalid = {**body, "answers": answers(lesson, "game", False)}
    assert client.post("/api/attempts", json=invalid).status_code == 409
    assert client.get("/api/progress").json()["xp"] == 20


def test_content_revisions_preserve_snapshot_and_reject_invalid_publish(setup):
    client, app, _, content = setup
    original = complete(client)
    path = content / "lessons" / "L01.json"
    updated = {**original, "version": 2, "prediction": "Try a clearer example."}
    path.write_text(json.dumps(updated), encoding="utf-8")
    assert client.post("/api/content/reload", json={}).status_code == 200
    summary = client.get("/api/progress").json()
    assert summary["xp"] == 80 and summary["lessons"]["L01"]["completed"]
    assert summary["lessons"]["L01"]["updated"] and summary["lessons"]["L01"]["game"]
    updated["version"] = 3
    updated["game"]["rounds"][0]["id"] = "L01-game-r1-new"
    path.write_text(json.dumps(updated), encoding="utf-8")
    assert client.post("/api/content/reload", json={}).status_code == 200
    summary = client.get("/api/progress").json()
    assert summary["lessons"]["L01"]["completed"] and not summary["lessons"]["L01"]["game"]
    assert summary["xp"] == 80
    updated["game"]["rounds"][0]["feedback"] = {}
    path.write_text(json.dumps(updated), encoding="utf-8")
    assert client.post("/api/content/reload", json={}).status_code == 400
    assert client.get("/api/lessons/L01").json()["version"] == 3
    assert app.state.progress.summary()["xp"] == 80


def test_content_registry_prerequisites_and_json_schema(setup):
    _, _, _, content = setup
    path = content / "lessons" / "L01.json"
    lesson = json.loads(path.read_text(encoding="utf-8"))
    lesson["game"]["type"] = "unregistered_renderer"
    path.write_text(json.dumps(lesson), encoding="utf-8")
    with pytest.raises(ContentError):
        ContentStore(content)
    course = json.loads((content / "course.json").read_text(encoding="utf-8"))
    course["lessons"][0]["prerequisites"] = ["L02"]
    (content / "course.json").write_text(json.dumps(course), encoding="utf-8")
    with pytest.raises(ContentError, match="prerequisites"):
        ContentStore(content)
    (content / "lesson.schema.json").write_text('{"type": "unknown-json-schema-type"}', encoding="utf-8")
    with pytest.raises(ContentError, match="Could not load course"):
        ContentStore(content)


def test_demo_no_network_and_safe_output(setup, monkeypatch):
    import socket
    client, *_ = setup
    def forbidden(*args, **kwargs):
        raise AssertionError("M1 must not call a provider")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    response = client.post("/api/demo/messages", json={"message": "What is a token?"})
    assert response.json()["network_calls"] == 0
    assert response.json()["mode"] == "demo" and "text" in response.json()["reply"]
    assert not client.get("/api/provider/status").json()["connected"]
    assert client.post("/api/demo/messages", json={"message": " "}).status_code == 422
    assert client.post("/api/demo/messages", json={"message": "a" * 2001}).status_code == 422
    script = "<script>window.bad=true</script>"
    client.post("/api/journal", json={"lesson_id": "L01", "changed": script, "learned": "Escaping works"})
    assert script not in client.get("/workshop").text
    assert "&lt;script&gt;" in client.get("/workshop").text


def test_local_request_guards(setup):
    client, *_ = setup
    assert client.post("/api/demo/messages", json={"message": "Hi"}, headers={"Origin": "https://unrelated.example"}).status_code == 403
    assert client.post("/api/demo/messages", content='{"message":"hi"}', headers={"Content-Type": "text/plain"}).status_code == 415
    assert client.get("/", headers={"Host": "unrelated.example"}).status_code == 400
    assert "frame-ancestors 'none'" in client.get("/").headers["Content-Security-Policy"]
