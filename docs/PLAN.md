# Build and learning plan

Created: 1 October 2026. Working name: **Tiny Chat Lab**.

Current status: **M0 and M1 complete.** The local learning app is implemented and verified. See [the M1 walkthrough](M1_WALKTHROUGH.md) and [verification record](M1_VALIDATION.md). M2 software is implemented and locally tested; its actual-credential connection gate remains open. See [M2 walkthrough](M2_WALKTHROUGH.md) and [M2 verification](M2_VALIDATION.md).

M3 software is now implemented with saved chats, personas, multi-turn context, streaming, Stop, retry variants, and L10–L12. See [M3 walkthrough](M3_WALKTHROUGH.md) and [M3 verification](M3_VALIDATION.md). The requested next implementation proceeded using local demo/mock proof; real Google gates for M2/M3 remain open.

M4 is implemented with three local numeric toys and L13–L15. See [M4 walkthrough](M4_WALKTHROUGH.md) and [M4 verification](M4_VALIDATION.md). M5 is the next planned implementation. This software status does not imply a learner has completed the exercises.

## Outcome

Build a playful web app that teaches LLMs and helps you construct a small ChatGPT-style assistant. Every session should end with a concept you can explain and an artifact you can show: a Python function, a better prompt, a saved chat, or a working feature.

The app has two personalities: a patient tutor that helps you learn, and your own chatbot that you build and experiment with. They use separate instructions, conversations, and progress rules.

## Scope and assumptions

- One learner on a local machine first. Basic Python experience; no ML prerequisites.
- Short sessions: about 20–35 minutes for a lesson, with longer build sessions when needed.
- Python drives the backend. HTML/CSS and a little JavaScript are introduced gradually.
- Google Cloud / Vertex AI is the selected provider. Credentials stay on the server.
- Fifteen complete lessons are available now; the remaining nine have planned objectives and activities.
- Progress persists between sessions. Content grows when you ask for additions or changes.
- No calendar pressure: use session numbers, not deadlines. Roughly 20–35 hours for the full core path including builds, depending on practice and debugging.

Success means you can explain next-token prediction, distinguish training from inference, manage conversation context, call a hosted model, evaluate responses, and understand why a chatbot can be confidently wrong. You also have a local app with a course reader, games, tutor, saved chats, and a basic note-grounded chatbot.

## The session loop

1. **Predict:** guess what a small example will do before seeing the explanation.
2. **Learn:** read one plain-language idea and one everyday analogy.
3. **Play:** complete a short game with explanations for every answer.
4. **Build:** change or write a small piece of Python or one app feature.
5. **Explain:** answer three questions and describe the idea in your own words.
6. **Save:** record completion and a short project journal entry.

Ask AI is available throughout, with buttons for “Give me a hint,” “Use a simpler example,” and “Explain this Python.” Hints come before full solutions by default. A learner may request a worked solution at any time.

## Stages and completion gates

| Milestone | Deliverable | Learning focus | Gate |
| --- | --- | --- | --- |
| M0: plan and seed | These docs; course map; six full lessons; structured content | What we are building | Content check passes; authored versus outlined lessons distinguished |
| M1: playable local shell | Home, reader, games, quizzes, progress, demo chat | L01–L06; request/response basics | All six lessons usable; reload preserves progress; demo clearly labeled |
| M2: real AI | Vertex adapter, connection check, Ask AI, one real chat reply | L07–L09 authored during this stage | Connection works with the user's actual auth mode; secrets stay server-side; failures recover |
| M3: your small chatbot | Multi-turn context, persona, streaming, stop, saved chats, usage | L10–L12 | Follow-up references earlier messages; restart loads chats; stop preserves partial status |
| M4: understand the internals | Embedding toy, attention table, tiny-model learning activities | L13–L15 | Learner can distinguish these educational toys from the hosted model |
| M5: answers from your notes | Small curated note library, retrieval, source references, no-evidence behavior | L16–L18 | Relevant notes retrieved; fabricated citations rejected; unsupported question gets uncertainty |
| M6: reliability | Tool sandbox, injection exercise, evaluation report | L19–L21 | Tools use allowlists; fixed evaluation set runs; untrusted notes cannot trigger execution |
| M7: finish and explain | Capstone, export/backup, optional deployment checklist | L22–L24 | Local acceptance checklist passes; learner explains the full request flow |

Finish each stage before adding its successor. M1 is a useful app even without Google access. M2 and M3 produce the first real ChatGPT-style experience. Retrieval and agent tools are later learning goals.

## First implementation slice: M1

Implement the smallest complete loop: open a lesson, make a prediction, run a game, answer a quiz, mark a build task, and return later with progress intact.

Use FastAPI + Jinja templates, native CSS, and plain JavaScript modules. Store progress in SQLite. Load lessons from JSON; do not hardcode lesson text into templates. The home screen shows “Continue L01,” six available lessons, and the rest of the map as “Coming in a later session.”

Build a three-message demo chat with deterministic replies. It must say “Demo: no model connected” and must never present simulated output as an AI response. Include Ask AI's disconnected state, provider settings summary, and a button that explains how M2 will enable it.

Do not include executable browser Python in M1. Code examples have Copy and expected-output controls; the learner runs them locally. Editable snippets can be copied into local files. Later browser execution requires a distinct, isolated design.

### Learning roles during development

The assistant scaffolds infrastructure and explains the code. The learner takes one small ownership task per session: alter a dictionary, add a game round, build a prompt, or wire a function. Tasks have a starter, hints, and a reference solution. If you ask for a full implementation, build it and then offer a “change one thing” exercise; do not hold the project hostage to a quiz.

At the end of a build session, report what works, show one important request path, list the next concept, and update the journal and backlog. Avoid introducing multiple unfamiliar frameworks at once.

## How future prompts evolve the course

There are two phases:

- **During development:** you prompt the coding assistant in this chat. It updates lesson JSON and docs, verifies the changes, and records a revision. This is the primary workflow for the first release.
- **Inside the app, later:** an optional course-editing workspace asks AI to propose structured lesson revisions. Drafts are validated and previewed before the learner publishes them. Asking the tutor a question never silently changes the course.

Typical requests: “Make tokens easier,” “Add a cricket example,” “Continue with the next three lessons,” “Add a game for embeddings,” or “Explain this lesson in Bangla.” Each affects only the relevant content unless you request a larger rewrite.

Keep stable lesson and activity IDs. Preserve completed work. Mark substantially changed material “Updated: optional review.” When the learning objective changes, create a new activity ID or successor lesson. The content contract defines migration and rollback rules.

## Completion rules

MVP completed: six working lessons, games, quizzes, persistent progress, real Ask AI, and a basic live chatbot with readable error states. This spans M1–M2. The fuller small chatbot arrives at M3; the complete core course ends at M7.

A working chatbot alone does not count as a finished learning app. A pretty learning map alone does not count either. The learner must be able to learn, experiment, ask for help, save progress, and build something.

## Future expansions

Optional after the core path: a tiny character-level transformer in PyTorch, supervised fine-tuning concepts, voice chat, browser Python through an isolated worker, multilingual lesson packs, and multiple learners. No GPU, vector database, managed agent runtime, or paid deployment is required for the initial milestones.
