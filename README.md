# Tiny Chat Lab

Learn how LLMs work by playing short games and building your own small chatbot.

This project is designed for someone who can read basic Python: variables, lists, dictionaries, loops, and functions. You do not need machine learning experience. The plan starts with familiar examples and introduces math only when it explains something useful.

**Current deliverable: M5 is implemented.** Eighteen complete lessons work offline, with the Model Observatory and a new Knowledge Library. Split practice notes, inspect keyword search, and read exact source quotes. Optional Google mode selects checked evidence using the same Settings connection and request limits. Saved chats, streaming, Stop, variants, and the lesson tutor remain available. Start with [the M5 walkthrough](docs/M5_WALKTHROUGH.md); see [M5 verification](docs/M5_VALIDATION.md). Actual Google access still needs your explicit connection test.

## Run the app

Open [Tiny Chat Lab](http://127.0.0.1:8001) while the server is running. From this project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -c requirements.lock.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8001
```

The environment is already installed in this workspace. `./run.ps1` starts the app too; `./run.ps1 -Port 8002` selects another port. Tested on Python 3.14.7. Keep this local server on loopback. The separate [Vercel deployment guide](docs/VERCEL_DEPLOYMENT.md) describes private hosting with durable cloud storage.

Progress, journals, saved Demo/Google chats, persona settings, variants, and usage live in the ignored `data/tiny-chat.db`. Unsent drafts stay in browser tab storage. Only selected recent turns from the current chat enter a chatbot request. No Google account is required for offline learning or the clearly labeled Python memory/stream rehearsal.

## Connect from Settings

Open [Settings](http://127.0.0.1:8001/settings), paste your Google Cloud express API key in the password field, choose a model, and click **Save connection**. Then **Test Google connection** to verify access. No configuration file or server restart is needed. Saved keys are encrypted for your Windows account; a blank field keeps the key and **Remove saved key** clears it and disables AI. Standard Cloud ADC remains available in the same form. See [the setup walkthrough](docs/M2_WALKTHROUGH.md).

## Start here

1. Start with [the M1 walkthrough](docs/M1_WALKTHROUGH.md), or continue to [the M2 experiments and setup](docs/M2_WALKTHROUGH.md).
2. Try [the starter lessons](docs/STARTER_LESSONS.md). Each contains an explanation, game, runnable Python example, quiz, and build mission.
3. Use [the prompt playbook](docs/PROMPT_PLAYBOOK.md) to start building or request changes over time.

Every authored lesson now includes an animated visual story beside its matching Python. Watch inputs turn into results, pause on highlighted lines, and try a short hunch game. Begin with [the visual learning walkthrough](docs/VISUAL_LESSONS.md).

## What we will build

Two connected spaces: **Learn** teaches one concept at a time; **Build** turns those concepts into a chatbot with conversation history, streaming replies, a persona, and eventually answers from your own notes. A separate **Ask AI** tutor helps with the current lesson through Google Cloud / Vertex AI.

We will build an application around a pretrained model. We will also build tiny Python prediction models to understand the mechanism. Training a large model from scratch is a separate optional learning track.

## Document map

| Document | What it answers |
| --- | --- |
| [Plan](docs/PLAN.md) | What do we build first, and how do we learn while building? |
| [M1 walkthrough](docs/M1_WALKTHROUGH.md) | How do I use the app and understand its Python request flow? |
| [M1 verification](docs/M1_VALIDATION.md) | What was tested in the first milestone? |
| [M2 walkthrough](docs/M2_WALKTHROUGH.md) | How do I connect Google and learn the model request path? |
| [M2 verification](docs/M2_VALIDATION.md) | What works, and what still needs a live account check? |
| [M3 walkthrough](docs/M3_WALKTHROUGH.md) | How do saved context, personas, streams, Stop, and reply variants work? |
| [M3 verification](docs/M3_VALIDATION.md) | What proves local behavior, and which live checks remain? |
| [M4 walkthrough](docs/M4_WALKTHROUGH.md) | How do vectors, attention, and a training update work? |
| [M4 verification](docs/M4_VALIDATION.md) | What proves the numeric toys and expanded learning flow? |
| [M5 walkthrough](docs/M5_WALKTHROUGH.md) | How do chunks, retrieval, and checked evidence work? |
| [M5 verification](docs/M5_VALIDATION.md) | What proves Library behavior and its limitations? |
| [Settings verification](docs/SETTINGS_VALIDATION.md) | How are saved keys protected and connection changes tested? |
| [Vercel deployment](docs/VERCEL_DEPLOYMENT.md) | How does the private cloud lab preserve progress, chats, and Settings? |
| [Product requirements](docs/PRODUCT.md) | What must each screen and feature do? |
| [Curriculum](docs/CURRICULUM.md) | What are the 24 lessons, games, and build tasks? |
| [Starter lessons](docs/STARTER_LESSONS.md) | What can I learn right now? |
| [Content contract](docs/CONTENT_CONTRACT.md) | How do lessons, progress, and revisions fit together? |
| [Prompt playbook](docs/PROMPT_PLAYBOOK.md) | What should I ask next, and what happens to the content? |
| [Architecture](docs/ARCHITECTURE.md) | How will the Python app, browser, database, and AI connect? |
| [Google integration](docs/GOOGLE_INTEGRATION.md) | How will my Vertex AI key or Cloud credentials be used? |
| [Design](docs/DESIGN.md) | How will the learning experience feel playful and usable? |
| [UI verification](docs/UI_VALIDATION.md) | What was checked in the studio redesign and motion update? |
| [Visual lessons](docs/VISUAL_LESSONS.md) | How do the 73 scenes explain Python, and how were they verified? |
| [Backlog](docs/BACKLOG.md) | What are the implementation tasks and completion criteria? |
| [Validation](docs/VALIDATION.md) | How will we know it works and teaches the right concepts? |
| [Decisions](docs/DECISIONS.md) | Which choices are settled and which depend on later information? |
| [Learning journal](docs/LEARNING_JOURNAL.md) | How do I record what I learned and built? |
| [Changelog](docs/CHANGELOG.md) | What changed in the course or plan? |

## Content and checks

- `content/course.json`: the full learning path, with honest authored/outline statuses.
- `content/lessons/*.json`: eighteen complete lessons; the authoritative lesson text.
- `content/library.json`: four curated café notes used by the Knowledge Library.
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

The plan uses Google Cloud / Vertex AI because you selected it. Cloud express keys and standard Cloud ADC are implemented; actual credentials and model access still need a real test. Official references are in [Google integration](docs/GOOGLE_INTEGRATION.md).

## Application checks

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt -c requirements.lock.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe tools/browser_check.py
.\.venv\Scripts\python.exe tools/browser_visual_check.py
.\.venv\Scripts\python.exe tools/browser_ai_check.py
.\.venv\Scripts\python.exe tools/browser_chat_check.py
.\.venv\Scripts\python.exe tools/browser_labs_check.py
.\.venv\Scripts\python.exe tools/browser_library_check.py
.\.venv\Scripts\python.exe tools/browser_settings_check.py
.\.venv\Scripts\python.exe tools/design_check.py
```

Browser checks use isolated databases and do not change your progress. The documentation check remains `python tools/verify_docs.py`. Eighteen matching Python examples, a 108-round Chromium learning flow, separate FAKE-provider tutor/chat flows, and mocked SDK streaming verify software behavior. A real Google connection still needs credentials; see the M5 verification record.
