# Course and project changelog

## 1 October 2026: M3 software

- Added schema-v3 saved conversations/personas, selected multi-turn context, streaming snapshots, Stop, recovery, explicit reply variants, and reversible archive/restore.
- Shared Google reservation/rate limits across tutor, single-turn, and saved-chat paths. Added structured SDK streaming with visible-text filtering and actual input counting.
- Authored L10, L11, and L12 version 1 with stable game/quiz/build IDs; course version 3 now has twelve lessons and 72 rounds. Earlier lesson versions and awards are unchanged.
- Added an M3 teaching walkthrough and backend/browser proof. Live Google acceptance remains pending actual credentials; see [M3 verification](M3_VALIDATION.md).

## 1 October 2026: studio redesign

- Added a cream/sage/teal palette with citrus and coral accents, self-hosted fonts, a custom robot, and illustrated learning zones.
- Improved reading hierarchy, responsive lesson navigation, and compact Play/Quiz covers.
- Added native page and feedback motion, brief XP celebrations, and a persistent motion control that honors reduced motion.
- Preserved lesson content, progress, scoring, and Google request behavior. See [UI verification](UI_VALIDATION.md) for responsive, interaction, and contrast evidence.

## 1 October 2026: M1 implemented

- Built the Python FastAPI/Jinja app with responsive Learn, Build, My chatbot, and Settings screens.
- Made all six authored games and quizzes playable with round-by-round feedback, study mode, retries, and server scoring.
- Added SQLite progress, completion snapshots, once-only XP, build acknowledgments, and learning journal entries.
- Added a deterministic demo chatbot, safe message rendering, tab-scoped drafts, and a disconnected Ask AI dialog.
- Added validated content reloads that preserve existing progress and reject malformed updates.
- Added runtime/dev dependency pins, a full environment lock, a local run helper, and the M1 teaching walkthrough.
- Verified 15 backend tests and a Chromium flow completing six lessons/36 rounds; tested mobile/reflow layouts and keyboard interactions.
- Google calls, live tutoring, persistent AI chat, browser Python, and content draft publishing remain later work.

## 1 October 2026: initial planning edition

- Defined Tiny Chat Lab, the playful lesson/build loop, and eight learning zones.
- Planned 24 lessons and M0–M7 build milestones.
- Authored L01–L06 with games, runnable Python, quizzes, missions, and feedback.
- Selected Google Cloud / Vertex AI based on the learner's reply; documented credential-mode verification.
- Added product, design, architecture, content/revision, prompt, backlog, and validation docs.
- Added structured content and local documentation tools.
- No application implementation or live provider verification yet.

Future entries should list affected lesson/activity IDs, version changes, validation evidence, and whether progress needs optional review.
