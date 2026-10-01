# Prompt-driven learning and building

## Initial prompt: completed in this planning session

Create the learning path, product plan, implementation stages, lesson contract, and first six complete lessons. Save them in this project. Seed a course map that distinguishes available lessons from future outlines. Use simple Python, practical games, and a build task in every lesson.

## Use these next

### Start building the app

> Read README.md and docs/PLAN.md. Build M1 of Tiny Chat Lab with FastAPI, Jinja, native CSS, and small JavaScript modules. Use content/lessons as the lesson source. Make the six games and quizzes playable, persist progress in SQLite, and include a labeled demo chat. Explain one important backend file and give me a small Python task. Verify the relevant user flows and update the backlog and changelog.

### Connect Google Cloud

> Implement M2 using Google Cloud / Vertex AI as described in docs/GOOGLE_INTEGRATION.md. Check which auth mode my credentials support without exposing secrets. Add a connection test, lesson-aware Ask AI, and one real chatbot response. Configure secrets locally on the server; do not ask me to paste them into a chat message. Teach me how the request travels from the browser to Google and back. Expand L07–L09 into complete lessons.

### Continue learning

> Continue from my saved progress. Teach the next lesson using one simple example, a prediction game, a short Python exercise, and a quiz. Ask me to predict before revealing the answer. End with one change I can make to my chatbot.

### Expand future content

> Fully author L10–L12 using the existing lesson contract. Keep the Python level approachable, use restaurant and cricket examples, and connect each build mission to M3. Preserve stable IDs and completed work. Validate the new content, regenerate the reading copy, and record the revision.

### Simplify a difficult concept

> Update L04 because tokens are still confusing. Keep its goal and IDs, use “building blocks of text” as the main analogy, explain why pieces are not always words, and add clearer feedback to the game. Preserve my progress and show what changed.

### Change the example without changing the concept

> Replace the snack examples in L05 with a cricket commentary example. Keep the sampling explanation accurate and avoid suggesting temperature improves factual accuracy. Preserve the quiz objectives and mark any new question IDs explicitly.

### Add a new lesson or game

> Add an optional lesson after L18 about why source citations can be wrong. Include a game that checks whether each claim is actually supported by a quoted note. Assign a new ID and do not change existing completion requirements.

### Request a worked solution

> I tried the L03 mission. Show the complete solution, explain it line by line, then give me one small variation to solve myself. Record the game as studied if I used the revealed answer; let me retry later.

### Learn in another language

> Help me learn L06 in Bangla with English technical terms in brackets. First give me a translated reading draft. If I ask to save it as an app language option, extend the locale contract and preserve the original lesson IDs and XP.

### Check understanding

> Quiz me on training versus inference using three fresh examples. Do not reveal answers until I respond. Explain each mistake and suggest the smallest review exercise. Do not modify official lesson progress unless I complete its authored quiz in the app.

### Review the project

> Review the current milestone against its completion gate. Tell me what works, what remains, and one technical idea I should explain in my own words. Update the journal template and backlog without adding unrelated features.

## What an update response must include

- What changed and which lesson/activity IDs were affected.
- A brief explanation of the concept and one example.
- Files updated and checks run.
- Any effect on progress, with preservation as the default.
- One next learning or build action.

## Development assistant working instructions

Read the docs and current content before changes. Check actual app state rather than claiming a planned feature exists. Make one coherent milestone or lesson update at a time. Explain unfamiliar Python syntax when it first appears. Prefer deterministic games and rubric checks to asking an LLM to decide whether the learner passed.

Respect the learner's pace. If they request implementation, complete the authorized implementation. If they request a lesson, teach it and make the activity concrete. If they request content changes, update the saved course instead of only describing a possible change.

Do not start autonomous scheduled lesson generation. Content evolves in response to learner prompts. Future in-app publishing follows the draft-and-preview workflow in the content contract.
