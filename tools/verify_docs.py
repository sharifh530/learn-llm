"""Verify this planning package; never use this to execute imported AI drafts.

Only explicitly reviewed lesson examples are executed, in fresh Python
processes with a short timeout. This is not a sandbox for untrusted code.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from render_lessons import OUTPUT, ROOT, render


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def schema_check(value, schema: dict, root_schema: dict, location: str) -> None:
    """Enforce only the JSON Schema keywords used by the initial contract."""
    if "$ref" in schema:
        target = root_schema
        for part in schema["$ref"].removeprefix("#/").split("/"):
            target = target[part]
        schema_check(value, target, root_schema, location)
        return
    if "const" in schema:
        require(value == schema["const"], f"{location}: incorrect constant")
    if "enum" in schema:
        require(value in schema["enum"], f"{location}: unsupported value")
    kind = schema.get("type")
    valid = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": type(value) is int,
    }
    if kind:
        require(valid[kind], f"{location}: expected {kind}")
    if kind == "object":
        for key in schema.get("required", []):
            require(key in value, f"{location}: missing {key}")
        require(len(value) >= schema.get("minProperties", 0), f"{location}: too few properties")
        properties = schema.get("properties", {})
        extra = schema.get("additionalProperties", True)
        for key, child in value.items():
            if key in properties:
                schema_check(child, properties[key], root_schema, f"{location}.{key}")
            elif extra is False:
                raise ValueError(f"{location}: unknown field {key}")
            elif isinstance(extra, dict):
                schema_check(child, extra, root_schema, f"{location}.{key}")
    elif kind == "array":
        require(len(value) >= schema.get("minItems", 0), f"{location}: too few items")
        require(len(value) <= schema.get("maxItems", float("inf")), f"{location}: too many items")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, sort_keys=True) for item in value]
            require(len(set(encoded)) == len(encoded), f"{location}: duplicate items")
        for index, child in enumerate(value):
            if "items" in schema:
                schema_check(child, schema["items"], root_schema, f"{location}[{index}]")
    elif kind == "string":
        require(len(value) >= schema.get("minLength", 0), f"{location}: empty text")
        if "pattern" in schema:
            require(re.search(schema["pattern"], value) is not None, f"{location}: pattern mismatch")
    elif kind == "integer":
        require(value >= schema.get("minimum", -float("inf")), f"{location}: too small")
        require(value <= schema.get("maximum", float("inf")), f"{location}: too large")


def main() -> None:
    course = json.loads((ROOT / "content" / "course.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "content" / "lesson.schema.json").read_text(encoding="utf-8"))
    entries = {entry["id"]: entry for entry in course["lessons"]}
    require(len(entries) == len(course["lessons"]) >= 24, "Expected at least 24 unique map entries")
    require({f"L{number:02}" for number in range(1, 25)} <= set(entries), "Core map entries missing")
    require(len(course["zones"]) >= 8, "Expected at least eight zones")
    grouped = [lesson_id for zone in course["zones"] for lesson_id in zone["lessons"]]
    require(len(grouped) == len(set(grouped)) == len(entries) and set(grouped) == set(entries), "Zone map mismatch")
    order = {identity: index for index, identity in enumerate(entries)}

    visited, visiting = set(), set()

    def visit(lesson_id: str) -> None:
        require(lesson_id in entries, f"Missing prerequisite {lesson_id}")
        require(lesson_id not in visiting, f"Prerequisite cycle at {lesson_id}")
        if lesson_id in visited:
            return
        visiting.add(lesson_id)
        for prerequisite in entries[lesson_id]["prerequisites"]:
            require(prerequisite in order and order[prerequisite] < order[lesson_id],
                    f"Prerequisite must be earlier in the course map: {lesson_id}/{prerequisite}")
            visit(prerequisite)
        visiting.remove(lesson_id)
        visited.add(lesson_id)

    for lesson_id in entries:
        visit(lesson_id)

    authored = [entry for entry in entries.values() if entry["status"] == "authored"]
    seed_ids = {f"L{i:02}" for i in range(1, 7)}
    # Explicitly reviewed, offline-only examples; do not execute arbitrary future content.
    trusted_examples = seed_ids | {"L07", "L08", "L09", "L10", "L11", "L12", "L13", "L14", "L15"}
    require(seed_ids <= {entry["id"] for entry in authored}, "Initial six lessons missing")
    for entry in entries.values():
        require(entry["status"] in {"authored", "outline"}, "Unknown content status")
        if entry["status"] == "outline":
            require("path" not in entry, "Outline must not pretend to have authored content")
    all_ids, question_count, example_count, skipped_examples = set(), 0, 0, []
    for entry in authored:
        path = ROOT / "content" / entry["path"]
        require(path.resolve().is_relative_to((ROOT / "content" / "lessons").resolve()), "Lesson path escaped content")
        lesson = json.loads(path.read_text(encoding="utf-8"))
        schema_check(lesson, schema, schema, entry["id"])
        require(lesson["id"] == entry["id"] and path.stem == entry["id"], "Lesson filename/ID mismatch")
        require(lesson["title"] == entry["title"], "Map title differs from authored lesson")
        require(lesson["prerequisites"] == entry["prerequisites"], "Prerequisite mismatch")
        zone = next(zone for zone in course["zones"] if lesson["id"] in zone["lessons"])
        require(lesson["zone"] == zone["title"], "Zone title mismatch")
        ids = [lesson["id"], lesson["game"]["id"], lesson["quiz"]["id"], lesson["build"]["id"]]
        questions = lesson["game"]["rounds"] + lesson["quiz"]["questions"]
        for question in questions:
            ids.append(question["id"])
            choice_ids = [choice["id"] for choice in question["choices"]]
            require(len(choice_ids) == len(set(choice_ids)), f"Duplicate choice: {question['id']}")
            require(question["correct_choice_id"] in choice_ids, "Answer does not reference a choice")
            require(set(question["feedback"]) == set(choice_ids), "Feedback must cover exactly every choice")
            question_count += 1
        for identity in ids:
            require(identity not in all_ids, f"Duplicate stable ID {identity}")
            require(identity.startswith(lesson["id"]), f"ID not scoped to lesson: {identity}")
            all_ids.add(identity)
        code = lesson["python_example"]["code"]
        compile(code, f"{entry['id']}-example.py", "exec")
        if entry["id"] not in trusted_examples:
            skipped_examples.append(entry["id"])
            continue
        with tempfile.TemporaryDirectory(prefix="tiny-chat-example-") as temporary:
            script = Path(temporary) / "example.py"
            script.write_text(code, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-I", str(script)], cwd=temporary,
                capture_output=True, text=True, encoding="utf-8", timeout=5,
            )
        require(result.returncode == 0, f"{entry['id']}: example failed: {result.stderr}")
        require(result.stdout == lesson["python_example"]["expected_output"],
                f"{entry['id']}: output mismatch: {result.stdout!r}")
        example_count += 1
    file_ids = {path.stem for path in (ROOT / "content" / "lessons").glob("*.json")}
    require(file_ids == {entry["id"] for entry in authored}, "Authored files/map mismatch")
    link_count = 0
    for markdown in [ROOT / "README.md", *(ROOT / "docs").rglob("*.md")]:
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", markdown.read_text(encoding="utf-8")):
            if target.startswith(("https://", "http://", "#", "mailto:")):
                continue
            path_text = target.strip("<>").split("#")[0]
            require((markdown.parent / path_text).exists(), f"Broken local link in {markdown.name}: {target}")
            link_count += 1
    require(OUTPUT.exists() and OUTPUT.read_text(encoding="utf-8") == render(), "Reading copy needs regeneration")
    print(f"PASS: {len(entries)} map entries, {len(course['zones'])} zones, {len(authored)} authored lessons, {question_count} game/quiz rounds")
    print(f"PASS: {example_count} Python examples match expected output; {link_count} local document links resolve")
    print("PASS: content contract subset, IDs, feedback, prerequisites, and generated reading copy")
    if skipped_examples:
        print(f"Additional examples checked for syntax only: {', '.join(skipped_examples)}. Review and verify them separately.")
    print("For application checks, run pytest and tools/browser_check.py. Live Google verification requires credentials and a real connection test.")


if __name__ == "__main__":
    main()
