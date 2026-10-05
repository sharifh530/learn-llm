"""Validate a whole course before replacing the active content snapshot."""

from copy import deepcopy
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from app.models import LibraryData
from app.visuals import validate_visual


class ContentError(ValueError):
    pass


class ContentStore:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()
        self.course = {}
        self.lessons = {}
        self.reload()

    def reload(self):
        """Build a candidate locally. Only publish it when every check passes."""
        try:
            course = json.loads((self.directory / "course.json").read_text(encoding="utf-8"))
            library = LibraryData.model_validate_json((self.directory / 'library.json').read_text(encoding='utf-8')).model_dump()
            schema = json.loads((self.directory / "lesson.schema.json").read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(schema)
            entries = course["lessons"]
            ids = [entry["id"] for entry in entries]
            if len(ids) != len(set(ids)):
                raise ContentError("Course has duplicate lesson IDs.")
            ordered = {identity: position for position, identity in enumerate(ids)}
            grouped = [identity for zone in course["zones"] for identity in zone["lessons"]]
            if set(grouped) != set(ids) or len(grouped) != len(ids):
                raise ContentError("Each lesson must appear in exactly one zone.")
            if any(type(course["xp"].get(kind)) is not int or course["xp"][kind] < 0
                   for kind in ("reading", "game", "quiz", "build")):
                raise ContentError("XP values must be nonnegative integers.")
            lessons, stable_ids = {}, set()
            for entry in entries:
                identity = entry["id"]
                if entry["status"] not in ("authored", "outline"):
                    raise ContentError(f"{identity}: unknown availability status.")
                for prerequisite in entry["prerequisites"]:
                    if prerequisite not in ordered or ordered[prerequisite] >= ordered[identity]:
                        raise ContentError(f"{identity}: prerequisites must appear earlier in the course.")
                if entry["status"] == "outline":
                    continue
                path = (self.directory / entry["path"]).resolve()
                if not path.is_relative_to(self.directory / "lessons"):
                    raise ContentError(f"{identity}: lesson path must stay in content/lessons.")
                lesson = json.loads(path.read_text(encoding="utf-8"))
                errors = sorted(validator.iter_errors(lesson), key=lambda error: str(error.path))
                if errors:
                    error = errors[0]
                    raise ContentError(f"{identity}: {'/'.join(map(str, error.path))}: {error.message}")
                validate_visual(lesson)
                if lesson["id"] != identity or lesson["title"] != entry["title"]:
                    raise ContentError(f"{identity}: map and lesson identity/title differ.")
                if lesson["prerequisites"] != entry["prerequisites"]:
                    raise ContentError(f"{identity}: prerequisites differ from the map.")
                if lesson["game"]["type"] != "choice_rounds":
                    raise ContentError(f"{identity}: unsupported game renderer.")
                zone = next(zone for zone in course["zones"] if identity in zone["lessons"])
                if lesson["zone"] != zone["title"]:
                    raise ContentError(f"{identity}: zone name differs from the map.")
                activities = [lesson["id"], lesson["game"]["id"], lesson["quiz"]["id"], lesson["build"]["id"]]
                for question in lesson["game"]["rounds"] + lesson["quiz"]["questions"]:
                    activities.append(question["id"])
                    choice_ids = [choice["id"] for choice in question["choices"]]
                    if len(choice_ids) != len(set(choice_ids)):
                        raise ContentError(f"{question['id']}: duplicate choices.")
                    if question["correct_choice_id"] not in choice_ids or set(question["feedback"]) != set(choice_ids):
                        raise ContentError(f"{question['id']}: invalid answer or missing choice feedback.")
                for activity in activities:
                    if activity in stable_ids or not activity.startswith(identity):
                        raise ContentError(f"{identity}: duplicate or incorrectly scoped ID {activity}.")
                    stable_ids.add(activity)
                lessons[identity] = lesson
            if not lessons:
                raise ContentError("Publish at least one authored lesson.")
        except ContentError:
            raise
        except (OSError, ValueError, KeyError, TypeError, StopIteration, SchemaError) as error:
            raise ContentError(f"Could not load course: {error}") from error
        self.course, self.lessons, self.library = course, lessons, library
        return {"authored": len(lessons), "total": len(entries)}

    def lesson(self, identity):
        if identity not in self.lessons:
            raise KeyError(identity)
        return deepcopy(self.lessons[identity])
