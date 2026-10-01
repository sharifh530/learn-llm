# Tiny Chat Lab

Learn how LLMs work by playing short games and building your own small chatbot.

This project is designed for someone who can read basic Python: variables, lists, dictionaries, loops, and functions. You do not need machine learning experience. The plan starts with familiar examples and introduces math only when it explains something useful.

**Current deliverable: M1 is built.** The local web app includes six lesson readers, playable games and quizzes, persistent progress and XP, build missions, a learning journal, a clearly labeled demo chatbot, and the disconnected Ask AI experience. The 24-lesson map and project docs guide the next milestones. Google integration is planned for M2.

## Run the app

Open [Tiny Chat Lab](http://127.0.0.1:8001) while the server is running. From this project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -c requirements.lock.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8001
```

The environment is already installed in this workspace. `./run.ps1` starts the app too; `./run.ps1 -Port 8002` selects another port. Tested on Python 3.14.7. Keep the app on loopback; public hosting is a later milestone.

Progress and journals live in the ignored `data/tiny-chat.db`. The demo conversation and unsent drafts stay in browser tab session storage. No Google credential or account is required for M1.

## Start here

1. Read [the M1 walkthrough](docs/M1_WALKTHROUGH.md) and try your first experiment in the app.
2. Try [the starter lessons](docs/STARTER_LESSONS.md). Each contains an explanation, game, runnable Python example, quiz, and build mission.
3. Use [the prompt playbook](docs/PROMPT_PLAYBOOK.md) to start building or request changes over time.

## What we will build

Two connected spaces: **Learn** teaches one concept at a time; **Build** turns those concepts into a chatbot with conversation history, streaming replies, a persona, and eventually answers from your own notes. A separate **Ask AI** tutor helps with the current lesson through Google Cloud / Vertex AI.

We will build an application around a pretrained model. We will also build tiny Python prediction models to understand the mechanism. Training a large model from scratch is a separate optional learning track.

## Document map

| Document | What it answers |
| --- | --- |
| [Plan](docs/PLAN.md) | What do we build first, and how do we learn while building? |
| [M1 walkthrough](docs/M1_WALKTHROUGH.md) | How do I use the app and understand its Python request flow? |
| [M1 verification](docs/M1_VALIDATION.md) | What has actually been tested? |
| [Product requirements](docs/PRODUCT.md) | What must each screen and feature do? |
| [Curriculum](docs/CURRICULUM.md) | What are the 24 lessons, games, and build tasks? |
| [Starter lessons](docs/STARTER_LESSONS.md) | What can I learn right now? |
| [Content contract](docs/CONTENT_CONTRACT.md) | How do lessons, progress, and revisions fit together? |
| [Prompt playbook](docs/PROMPT_PLAYBOOK.md) | What should I ask next, and what happens to the content? |
| [Architecture](docs/ARCHITECTURE.md) | How will the Python app, browser, database, and AI connect? |
| [Google integration](docs/GOOGLE_INTEGRATION.md) | How will my Vertex AI key or Cloud credentials be used? |
| [Design](docs/DESIGN.md) | How will the learning experience feel playful and usable? |
| [Backlog](docs/BACKLOG.md) | What are the implementation tasks and completion criteria? |
| [Validation](docs/VALIDATION.md) | How will we know it works and teaches the right concepts? |
| [Decisions](docs/DECISIONS.md) | Which choices are settled and which depend on later information? |
| [Learning journal](docs/LEARNING_JOURNAL.md) | How do I record what I learned and built? |
| [Changelog](docs/CHANGELOG.md) | What changed in the course or plan? |

## Content and checks

- `content/course.json`: the full learning path, with honest authored/outline statuses.
- `content/lessons/*.json`: six complete starter lessons; the authoritative lesson text.
- `content/lesson.schema.json`: the planned validation contract for every published lesson.
- `tools/verify_docs.py`: dependency-free checks for the starter content, document links, and Python examples.

Run the documentation check from this directory:

```powershell
python tools/verify_docs.py
```

The starter lesson document is a generated reading copy of the JSON files. Edit the JSON first, then regenerate it using the documented tool. Future lessons will be authored when you request them; outline entries are not presented as finished lessons.

## Original M1 build prompt

This scope is now implemented. Keep the prompt as a record of the first milestone.

> Build milestone M1 from docs/PLAN.md for Tiny Chat Lab. Read the project docs first. Use Python FastAPI, Jinja templates, native CSS, and small JavaScript modules. Implement the home screen, lesson reader, the six starter games, quizzes, local progress, and a clearly labeled demo chatbot. Teach me the key files and give me one small Python task to complete. Keep live Google calls for M2.

The plan uses Google Cloud / Vertex AI because you selected it. Exact credential type and model availability will be checked when the live integration is implemented. Official references are in [Google integration](docs/GOOGLE_INTEGRATION.md).

## Application checks

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt -c requirements.lock.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe tools/browser_check.py
```

Browser checks use an isolated database and do not change your progress. The documentation check remains `python tools/verify_docs.py`. M1 was verified with 15 passing backend tests and a full Chromium learning flow; see the verification record for limits.
