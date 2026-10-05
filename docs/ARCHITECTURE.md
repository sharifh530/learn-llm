# Technical architecture

## Stack choice

Use a **Python FastAPI application** that serves **Jinja HTML templates**, native CSS, and small JavaScript modules. SQLite holds single-learner local state. JSON files hold lessons. This is a project design choice: it lets the learner follow one Python request path without learning React and a separate Node backend simultaneously. FastAPI supports this template arrangement through its documented template utilities. [FastAPI templates](https://fastapi.tiangolo.com/advanced/templates/).

Use the **Google Gen AI Python SDK (`google-genai`)** behind a provider adapter. Its documented surface includes text generation, streaming, and token counting. Keep model and auth settings configurable; verify the selected model and SDK version at implementation time. [SDK documentation](https://googleapis.github.io/python-genai/).

Target a supported Python version compatible with the pinned dependencies; verify the learner's installed version before setup. Use a virtual environment, pinned application dependencies, and Python's standard SQLite interface for M1. Add pytest and a browser testing tool when meaningful app behavior exists.

## Request flow

```mermaid
flowchart LR
    B[Browser: lessons, games, chats] --> F[FastAPI routes]
    F --> C[Validated JSON lessons]
    F --> P[Progress and chat services]
    P --> D[(SQLite)]
    F --> T[Tutor or chatbot context builder]
    T --> G[Google provider adapter]
    G --> V[Google Cloud / Vertex AI]
    F --> B
```

The browser never calls Google with a reusable credential. The backend loads the current lesson by ID and version, validates the request, builds bounded context, and calls the adapter. It returns sanitized app-level data, not raw SDK objects.

## Planned application layout

```text
app/
  main.py                  # App startup, routes, static files
  config.py                # Server environment and limits
  models.py                # Typed request/response contracts
  db.py                    # Connections and schema migrations
  services/
    content.py             # Validated lessons and course map
    progress.py            # Attempts, completion, XP ledger
    chat.py                # Conversation context and persistence
    tutor.py               # Lesson-aware tutor instructions
    usage.py               # Quotas, usage reservation and reconciliation
  providers/
    base.py                # Provider interface
    demo.py                # Explicit deterministic demo
    google_cloud.py        # SDK and auth adapter
  templates/               # Home, lesson, workshop, chat, settings
  static/css/
  static/js/               # Games, quiz, chat stream, tutor drawer
content/                   # Existing course and lesson files
data/                      # Ignored local SQLite and backups
tests/                     # Added with implementation
tools/                     # Content rendering and validation
```

M1 is implemented with a deliberately smaller layout: `app/main.py`, `config.py`, `models.py`, `content.py`, `progress.py`, `db.py`, and `demo.py`, plus templates and static assets. M2 adds `ai.py` for context, policy, and usage, and `providers.py` for the Google SDK. M3 adds `chat.py` for saved turns, persona/context selection, streaming workers, and recovery; it reuses the existing database and AI reservation policy.

## App API contract

| Route | Purpose | Milestone |
| --- | --- | --- |
| `GET /` | Home and continue action | M1 |
| `GET /lessons/{id}` | Lesson page | M1 |
| `GET /api/course` | Course map and availability | M1 |
| `GET /api/lessons/{id}` | Validated lesson content/version | M1 |
| `POST /api/attempts` | Score authored game/quiz answers on server | M1 |
| `POST /api/lessons/{id}/acknowledgments` | Read/build self-reports | M1 |
| `GET /api/progress` | Completion and XP summary | M1 |
| `POST /api/journal` | Save learner reflection | M1 |
| `GET /api/provider/status` | Masked configuration status; no network call | M2 |
| `POST /api/provider/test` | Explicit bounded connection test | M2 |
| `POST /api/tutor/messages` | Complete lesson-aware single-turn response | M2 |
| `POST /api/ai/messages` | Complete single-turn chatbot response | M2 |
| `POST /api/chats` | Create saved Demo or Google conversation | M3 |
| `GET /api/chats` | List active/archived chats by mode | M3 |
| `POST /api/chats/{id}/messages` | Persist turn and start/recover generation by request ID | M3 |
| `GET /api/chats/{id}` | Saved messages and statuses | M3 |
| `POST /api/generations/{id}/cancel` | Request cancellation | M3 |
| `POST /api/chats/{id}/settings` | Save title and persona for future requests | M3 |
| `POST /api/chats/{id}/archive`, `/restore` | Reversible local archive | M3 |
| `POST /api/chats/{id}/context` | Preview draft and selected context | M3 |
| `POST /api/chats/{id}/turns/{turn}/retry`, `/select` | Explicit latest-turn variants/selection | M3 |
| `GET /api/generations/{id}`, `/events` | Saved status or reconnectable SSE snapshots | M3 |
| `POST /api/course/drafts` | Structured content proposal | Later |
| `POST /api/course/drafts/{id}/publish` | Publish validated draft | Later |

`POST /api/tutor/messages` accepts lesson ID/version, mode, message, and request_id. M2 is single-turn; no history is sent. It does not accept client-supplied system instructions or authoritative lesson bodies. On version mismatch, load the selected known version or return a refresh-required error.

`POST /api/attempts` accepts lesson/version, activity ID, round-to-choice mapping, and an idempotency key. Validate answer references, calculate score, and commit attempt plus any first-time XP award in one transaction. Client-provided scores are ignored.

## M2 persistence

Schema version 2 appends `ai_requests` (attempt ID, payload hash, purpose, lesson ID, status, timestamp, calls attempted, returned usage, cached response, redacted error code). Existing progress, XP, and journals are untouched. One local server process is supported. On restart, running attempts become interrupted without automatic reruns. The request ledger is not selected conversation history.

## M3 persistence

Schema version 3 appends `chats` (mode, title, predefined persona, archive flag), `chat_turns` (user text and selected generation ID), and `generations` (variant text/status, immutable input context snapshot, usage and redacted errors). Live generations also reserve the existing `ai_requests` ledger. All prior learning rows remain unchanged. M3 uses one local server process. SQLite backup is taken before the local upgrade.

## Future database additions

- `chats`: ID, learner ID, mode (`tutor` or `chatbot`), persona version, timestamps.
- `messages`: ID, chat ID, role, content, status, active variant, timestamps.
- `generations`: ID, message ID, provider/model, status, error code, usage record.
- `usage_records`: input/output tokens if returned, estimation status, reserved budget, request ID.
- `settings`: non-secret learner preferences. Credentials live outside the database in M1–M3.

Use SQL parameters and a schema migration version. Use a stable local learner identity for the first version. Public hosting requires real access control and per-user ownership checks.

## Provider interface

Expose `generate`, `stream`, `count_tokens`, and `health_check`. Return normalized events/text, usage metadata if available, and app-level errors. Never silently fall back to demo replies after a live API failure. Choose demo mode explicitly.

Keep auth-mode selection separate from the generation interface. Tutor and chatbot can share a client pool while using different instructions, state, and input budgets.

## Context and streaming

M2 uses complete single-turn responses. M3 separates generation creation from stream reading: an idempotent POST saves/starts the attempt; `fetch` reads a GET SSE endpoint with `snapshot` and `done` events containing full saved generation text, status, and usage. This replaces the planned streamed POST/delta design because refresh can reconnect without replay offsets or a new paid attempt. A background worker persists chunks independently of the browser connection.

Select at most ten recent whole user/selected-assistant pairs using a labeled conservative UTF-8 byte heuristic for a 12,000-token input cap, including system instructions and the current message. Google counts the actual structured input before generation. Output is capped separately at 2,048 tokens. Older omitted turns stay saved. Never slice a message or include an orphan assistant reply.

Persist the user message and reservation before generation. Save accepted text chunks and finalize as `complete`, `stopped`, `failed`, `blocked`, or `truncated`; restart recovery adds `interrupted`. Partials are excluded until explicitly selected. Blocked text is cleared. Stop commits status immediately and signals the worker; conditional writes fence late chunks. Cancellation can wait for an in-flight SDK read, and the live reservation remains held until it unwinds. The browser reads a final snapshot and closes the stream. Upstream billing may already have occurred.

## Local and hosted boundaries

Bind the initial app to loopback. Render model/content text with escaping or a sanitizer and an allowed Markdown subset. Do not execute generated code. Use same-origin APIs, strict input sizes, and safe error messages. A hostile retrieved note cannot change permissions or authorize tools.

Before public hosting: add authentication, ownership checks, CSRF protection for cookie-based mutations, persistent storage strategy, server-side secret management, rate limits, usage budgets, and backup recovery. Local SQLite inside an ephemeral hosted container is insufficient; pick durable storage at that stage.

## Implemented M4 numeric path

`app/labs.py` contains pure standard-library calculations for three bounded educational toys. `SimilarityToy`, `AttentionToy`, and `TrainingToy` in `app/models.py` reject wrong dimensions, nonfinite or out-of-range numbers, unknown operations, and extra fields. Routes `POST /api/labs/similarity`, `/attention`, and `/training` return deterministic JSON. They never call the provider or write SQLite state. No database migration or new dependency was needed.

`GET /observatory` renders `observatory.html`; `labs.js` manages tabs, sliders, accessible meters, a loss plot/table, stale-response suppression, errors, and optional session storage. Explicit Train buttons apply updates; Predict reads the weight. Full-precision weight persists separately from the range input's rounded value. History resets on reload or manual weight changes and is bounded to 13 plotted states/12 table updates.

The optional lesson `lab` enum names a registered toy. Content remains schema validated; existing lesson JSON without `lab` remains valid. Earlier lesson versions and scoring IDs are unchanged. No generated code is executed by these routes.

## Connection settings · 2 October 2026

Settings now posts typed connection fields to `POST /api/provider/settings`; `POST /api/provider/key/remove` removes the key and disables AI. Status returns nonsecret fields and `key_saved` only. No AI configuration is loaded from environment files or variables. Windows DPAPI encrypts the credential in ignored `data/ai-settings.json`, which is atomically replaced before applying the new in-memory immutable settings and adapter. Failed validation/storage keeps the old connection. No plaintext fallback is used on other operating systems.

Admission locks and active-request accounting reject connection changes during tutor/connection calls and saved-chat workers. Saves reset verified status without calling Google. Settings survive restart, while unreadable storage opens the app offline with a recovery notice. SQLite learning/usage/chat data is unaffected. Local port access and processes running as the same Windows account remain within the trust boundary.

## Private Vercel deployment · 2 October 2026

`app/vercel.py` exports the hosted FastAPI entry point. Vercel Authentication
protects all deployments of this single-learner lab; every authorized visitor
shares one learner profile. `app/cloud_db.py` executes the existing parameterized
queries through Turso's HTTPS pipeline, with explicit transactions and no local
replica. Database setup adds tables without changing local Windows data.

Hosted AI and chat services are scoped to each request. Reservations and settings
checks share a database transaction. Google keys are entered in Settings and
encrypted by `app/cloud_settings.py`; hosting variables contain only infrastructure
configuration. A hosted SSE request claims the saved generation's worker lease
and owns its execution. Other requests observe snapshots, while Stop fences late
writes in the database. Local mode keeps its existing background workers.

See [Vercel deployment and rollback](VERCEL_DEPLOYMENT.md) for provisioning,
credential boundaries, live verification, and remaining checks.

## Knowledge Library · M5

`app/library.py` splits curated paragraphs into bounded chunks and ranks positive
keyword overlap. `ContentStore` validates `content/library.json` with the course
and lessons before publishing a new in-memory snapshot. Search returns at most
three chunks, their matched terms, source IDs, and the library fingerprint.
Scores describe word overlap, not answer confidence.

`GET /library` and `GET /api/library` expose the curated catalog.
`POST /api/library/chunks` provides a temporary preview without storing or adding
text to retrieval. `POST /api/library/search` returns the search trace;
`POST /api/library/answers` returns offline quotes or explicit Google selection.
The typed, same-origin mutation routes return uncached responses.

No matches means no provider call. In Google mode, only the question and up to
three retrieved chunks enter the existing `AIService` request path. A strict
validator accepts only unique retrieved IDs paired with their exact whole chunk
text, or an empty insufficient-evidence response. The browser displays checked
quotes rather than a free-form model answer. This proves source/text membership,
not relevance or truth. Invalid output is withheld while known usage remains
recorded. The existing request ledger, quota, Settings, and cloud transactions
apply; no database migration is needed. The context fingerprint also participates
in request identity so revised sources cannot reuse an old cached selection.

See [M5 walkthrough](M5_WALKTHROUGH.md) and [verification](M5_VALIDATION.md).
