# Lesson content and progress contract

## One source of lesson truth

Author lesson JSON under `content/lessons/`. The schema is `content/lesson.schema.json`. Generate `docs/STARTER_LESSONS.md` from these files using `python tools/render_lessons.py`. UI renderers consume the same JSON. The course map refers to lesson IDs and marks entries `authored` or `outline`.

Lesson fields: stable `id`, integer `version`, `status`, `title`, `zone`, `minutes`, `prerequisites`, `objectives`, `prediction`, `explanation`, `analogy_limit`, `python_example`, `game`, `quiz`, `build`, `reflection`, and `tutor_context`.

The six starter games deliberately share `choice_rounds`. Richer game types require a schema extension and a registered renderer before they can be published. A renderer registry rejects unknown types instead of silently substituting another game.

Each game and quiz has exactly three starter rounds with stable IDs, a correct choice ID, and a feedback string for every choice. `pass_correct` is two. The answer keys stay out of tutor prompts unless the learner explicitly requests the solution. This is learning software, so client-readable answer keys are acceptable; do not present them as protected examinations.

Build tasks include a stable ID, instructions, two or more observable completion criteria, graduated hints, and a reference solution. The initial app records learner acknowledgment rather than executing arbitrary Python.

## IDs and versions

Examples: `L04`, `L04-game`, `L04-game-r1`, `L04-quiz-r1`, and `L04-build`. IDs describe identity, not display order or wording. Version numbers increase whenever published lesson content changes. The initial six lessons are version 1.

| Revision | Treatment |
| --- | --- |
| Typo, example wording, clearer explanation | Keep IDs; bump lesson version; preserve all progress |
| Change a question's assessed concept or correct answer | New round ID; keep old attempts; offer review of the new round |
| Add optional exercise | New activity ID; preserve completion and earned XP |
| Replace a lesson objective | New lesson ID with `supersedes` in a future schema migration; retain old lesson/history |
| Move a lesson in the path | Keep ID; validate prerequisite graph; preserve progress |
| Translate a lesson | Future locale variant keyed by lesson ID/version/locale; do not create duplicate XP identity |

Version 1 of the schema does not yet support `supersedes` or translations. Extend and migrate the schema first when those features are requested.

## Progress data

Planned SQLite records:

- `lesson_progress`: learner ID, lesson ID, last seen version, completion timestamp, optional confidence.
- `activity_attempts`: learner ID, stable activity/round ID, lesson version, chosen answers, score, passed/studied state, timestamps.
- `xp_awards`: learner ID, activity ID, award type, amount, timestamp; unique on `(learner_id, activity_id, award_type)`.
- `journal_entries`: learner ID, lesson ID, text, timestamp.
- `content_revisions`: revision ID, parent revision, affected IDs, rationale, manifest checksum, published timestamp.

Use an immutable historical ledger for awarded XP. New content must not revoke awards or infer that old attempts assessed new questions. Lesson completion is a snapshot against the version completed. Display “Optional review available” when required activities change; keep that completion snapshot.

## Content update transaction

1. Parse the learner's request; identify target lesson/activity IDs and intended objective.
2. Draft changed JSON and accompanying course-map updates in a separate staging location.
3. Validate schema, unique IDs, answer references, feedback coverage, prerequisites, game registry, and code samples.
4. Produce a preview: before/after summary, changed concepts, progress effect, and source updates.
5. In development, an explicit editing request authorizes applying these reversible local changes after checks. Do not demand a second approval.
6. In the future in-app authoring workspace, draft generation and publishing are separate actions. The Publish button commits the validated draft and revision manifest atomically.
7. Update the reading copy and changelog. Keep the prior published content snapshot.

If validation fails, preserve the current published content and show the draft errors. A partial write never becomes published course content.

## Rollback

Restore the previous content snapshot, regenerate reading copies, and append a rollback revision referencing both snapshots. Do not erase progress, XP, chats, or attempts created since that snapshot. If IDs disappear from the visible course, retain their records for history and possible restoration.

## Generation boundaries

Ask AI answers are transient tutoring messages. A generated lesson is a draft until checked. Generated code is displayed as text; neither the content importer nor tutor executes it. Allow only known block/game types; no raw HTML, JavaScript, arbitrary URLs as executable assets, or hidden instructions from lesson content.

The authoring prompt includes the schema, learner level, specific requested change, target content, and relevant sources. It must not include API keys, unrelated chats, or the entire personal journal.
