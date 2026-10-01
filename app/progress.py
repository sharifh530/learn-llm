"""The server owns scoring, completion, and once-only XP awards."""

from datetime import datetime, timezone
import hashlib
import json


def now():
    return datetime.now(timezone.utc).isoformat()


def signature(activity):
    questions = activity.get("rounds", activity.get("questions"))
    identity = sorted((question["id"], question["correct_choice_id"]) for question in questions)
    return json.dumps(identity)


class ProgressError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


class ProgressService:
    def __init__(self, database, content):
        self.database = database
        self.content = content

    def check_version(self, lesson, version):
        if version != lesson["version"]:
            raise ProgressError("This lesson was updated. Refresh before saving a new attempt.", 409)

    def award(self, connection, identity, kind):
        amount = self.content.course["xp"][kind]
        cursor = connection.execute(
            "INSERT OR IGNORE INTO xp_awards VALUES (?, ?, ?, ?)", (identity, kind, amount, now())
        )
        return amount if cursor.rowcount else 0

    def complete_if_ready(self, connection, lesson):
        kinds = {row["kind"] for row in connection.execute(
            "SELECT kind FROM acknowledgments WHERE lesson_id = ?", (lesson["id"],)
        )}
        current_signatures = {lesson[kind]["id"]: signature(lesson[kind]) for kind in ("game", "quiz")}
        passed = {row["activity_id"] for row in connection.execute(
            "SELECT activity_id, question_signature FROM activity_progress WHERE lesson_id = ? AND passed = 1", (lesson["id"],)
        ) if row["question_signature"] == current_signatures.get(row["activity_id"])}
        ready = {"reading", "build"} <= kinds and {lesson["game"]["id"], lesson["quiz"]["id"]} <= passed
        if ready:
            connection.execute("""
                INSERT INTO lesson_progress (lesson_id, completed_version, completed_at)
                VALUES (?, ?, ?) ON CONFLICT (lesson_id) DO UPDATE SET
                completed_version = COALESCE(lesson_progress.completed_version, excluded.completed_version),
                completed_at = COALESCE(lesson_progress.completed_at, excluded.completed_at)
            """, (lesson["id"], lesson["version"], now()))

    def visit(self, lesson):
        with self.database.connection() as connection:
            connection.execute("""
                INSERT INTO lesson_progress (lesson_id, last_seen_version, last_seen_at) VALUES (?, ?, ?)
                ON CONFLICT (lesson_id) DO UPDATE SET
                last_seen_version = excluded.last_seen_version, last_seen_at = excluded.last_seen_at
            """, (lesson["id"], lesson["version"], now()))

    def acknowledge(self, lesson, kind, version):
        self.check_version(lesson, version)
        with self.database.connection() as connection:
            connection.execute("INSERT OR IGNORE INTO acknowledgments VALUES (?, ?, ?, ?)",
                               (lesson["id"], kind, version, now()))
            identity = lesson["build"]["id"] if kind == "build" else f"{lesson['id']}-reading"
            awarded = self.award(connection, identity, kind)
            self.complete_if_ready(connection, lesson)
        return {"award_added": awarded, "progress": self.summary()}

    def attempt(self, body):
        lesson = self.content.lesson(body.lesson_id)
        self.check_version(lesson, body.version)
        activity = next((lesson[kind] for kind in ("game", "quiz") if lesson[kind]["id"] == body.activity_id), None)
        if activity is None:
            raise ProgressError("That activity does not belong to this lesson.")
        questions = activity.get("rounds", activity.get("questions"))
        expected_ids = {question["id"] for question in questions}
        if not body.study and set(body.answers) != expected_ids:
            raise ProgressError("Answer every round before saving your attempt.")
        if not set(body.answers) <= expected_ids:
            raise ProgressError("Unknown question in this attempt.")
        feedback, score = [], 0
        for question in questions:
            choice = body.answers.get(question["id"])
            if choice is not None and choice not in {option["id"] for option in question["choices"]}:
                raise ProgressError("Unknown answer choice.")
            correct = choice == question["correct_choice_id"]
            score += int(correct)
            feedback.append({"id": question["id"], "correct": correct,
                             "correct_choice_id": question["correct_choice_id"],
                             "feedback": question["feedback"]})
        payload_hash = hashlib.sha256(json.dumps(body.model_dump(exclude={"idempotency_key"}), sort_keys=True).encode()).hexdigest()
        passed = score >= activity["pass_correct"] and not body.study
        result = {"score": score, "total": len(questions), "passed": passed, "studied": body.study,
                  "feedback": feedback, "award_added": 0}
        with self.database.connection() as connection:
            # Lock before checking idempotency or awarding XP: concurrent retries stay consistent.
            connection.execute("BEGIN IMMEDIATE")
            previous = connection.execute("SELECT * FROM attempts WHERE idempotency_key = ?", (body.idempotency_key,)).fetchone()
            if previous:
                if previous["payload_hash"] != payload_hash:
                    raise ProgressError("Retry key already belongs to another attempt.", 409)
                replay = json.loads(previous["response"])
                replay["replayed"] = True
                replay["award_added"] = 0
                return replay
            connection.execute("""
                INSERT INTO activity_progress VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (activity_id) DO UPDATE SET
                best_score = CASE WHEN activity_progress.question_signature = excluded.question_signature THEN MAX(activity_progress.best_score, excluded.best_score) ELSE excluded.best_score END,
                passed = CASE WHEN activity_progress.question_signature = excluded.question_signature THEN MAX(activity_progress.passed, excluded.passed) ELSE excluded.passed END,
                studied = CASE WHEN activity_progress.question_signature = excluded.question_signature THEN MAX(activity_progress.studied, excluded.studied) ELSE excluded.studied END,
                passed_version = CASE WHEN excluded.passed = 1 OR activity_progress.question_signature != excluded.question_signature THEN excluded.passed_version ELSE activity_progress.passed_version END,
                question_signature = excluded.question_signature
            """, (body.activity_id, lesson["id"], 0 if body.study else score, int(passed), int(body.study), body.version if passed else None, signature(activity)))
            if passed:
                kind = "game" if body.activity_id == lesson["game"]["id"] else "quiz"
                result["award_added"] = self.award(connection, body.activity_id, kind)
            connection.execute("INSERT INTO attempts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                               (body.idempotency_key, payload_hash, lesson["id"], body.activity_id, body.version,
                                json.dumps(body.answers), score, int(body.study), json.dumps(result), now()))
            self.complete_if_ready(connection, lesson)
        return result

    def summary(self):
        with self.database.connection() as connection:
            stored = {row["lesson_id"]: dict(row) for row in connection.execute("SELECT * FROM lesson_progress")}
            acknowledgments = {}
            for row in connection.execute("SELECT * FROM acknowledgments"):
                acknowledgments.setdefault(row["lesson_id"], set()).add(row["kind"])
            activities = {row["activity_id"]: dict(row) for row in connection.execute("SELECT * FROM activity_progress")}
            total_xp = connection.execute("SELECT COALESCE(SUM(amount), 0) FROM xp_awards").fetchone()[0]
            journal_count = connection.execute("SELECT COUNT(*) FROM journal_entries").fetchone()[0]
        lessons = {}
        for identity, lesson in self.content.lessons.items():
            record = stored.get(identity, {})
            acknowledgments_for_lesson = acknowledgments.get(identity, set())
            lesson_activities = {kind: activities.get(lesson[kind]["id"], {}) for kind in ("game", "quiz")}
            lesson_activities = {kind: state if state.get("question_signature") == signature(lesson[kind]) else {}
                                 for kind, state in lesson_activities.items()}
            completed = record.get("completed_at") is not None
            lessons[identity] = {
                "reading": "reading" in acknowledgments_for_lesson,
                "build": "build" in acknowledgments_for_lesson,
                "game": bool(lesson_activities["game"].get("passed")),
                "quiz": bool(lesson_activities["quiz"].get("passed")),
                "game_studied": bool(lesson_activities["game"].get("studied")),
                "quiz_studied": bool(lesson_activities["quiz"].get("studied")),
                "game_score": lesson_activities["game"].get("best_score", 0),
                "quiz_score": lesson_activities["quiz"].get("best_score", 0),
                "completed": completed,
                "completed_version": record.get("completed_version"),
                "updated": completed and record.get("completed_version") != lesson["version"],
            }
        ordered = [entry["id"] for entry in self.content.course["lessons"] if entry["id"] in lessons]
        next_id = next((identity for identity in ordered if not lessons[identity]["completed"]), ordered[-1])
        recent = sorted((record for record in stored.values() if record.get("last_seen_at") and record["lesson_id"] in lessons),
                        key=lambda record: record["last_seen_at"], reverse=True)
        if recent and not lessons[recent[0]["lesson_id"]]["completed"]:
            next_id = recent[0]["lesson_id"]
        badges = []
        if all(lessons.get(identity, {}).get("completed") for identity in ("L01", "L02", "L03")):
            badges.append("Prediction Explorer")
        if all(lessons.get(identity, {}).get("completed") for identity in ("L04", "L05", "L06")):
            badges.append("Context Keeper")
        return {"xp": total_xp, "completed": sum(state["completed"] for state in lessons.values()),
                "available": len(lessons), "lessons": lessons, "continue_id": next_id,
                "badges": badges, "journal_count": journal_count}

    def journals(self, lesson_id=None):
        with self.database.connection() as connection:
            if lesson_id:
                rows = connection.execute("SELECT * FROM journal_entries WHERE lesson_id = ? ORDER BY id DESC LIMIT 50", (lesson_id,))
            else:
                rows = connection.execute("SELECT * FROM journal_entries ORDER BY id DESC LIMIT 50")
            return [dict(row) for row in rows]

    def save_journal(self, body):
        self.content.lesson(body.lesson_id)
        with self.database.connection() as connection:
            cursor = connection.execute("INSERT INTO journal_entries (lesson_id, changed, learned, confusing, created_at) VALUES (?, ?, ?, ?, ?)",
                                        (body.lesson_id, body.changed.strip(), body.learned.strip(), body.confusing.strip(), now()))
            return dict(connection.execute("SELECT * FROM journal_entries WHERE id = ?", (cursor.lastrowid,)).fetchone())
