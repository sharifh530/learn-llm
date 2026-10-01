# Implementation backlog

Status: **M0 and M1 delivered. B01–B10 complete.** M2 implementation is present; B12 and the real-request gates in B13/B15 remain pending actual credential setup. B11, B14, B16, and B17 pass local checks. M3 and later remain planned. See [the M1 verification record](M1_VALIDATION.md) for actual checks and limits.

## M1: offline learning app

| ID | Task | Done when |
| --- | --- | --- |
| B01 | Python environment, dependency lock, app entry point | Local startup works with documented command and supported Python |
| B02 | Typed content loader and schema validation | Six lessons load; malformed content fails with a useful author error |
| B03 | Home, map, and availability | Authored lessons open; outline lessons clearly show future availability |
| B04 | Lesson reader and local-code panels | All sections render; copy and expected output work; HTML is escaped |
| B05 | Shared game renderer | All 18 game rounds score correctly and explain every choice |
| B06 | Quiz renderer | All 18 quiz questions score correctly; retries and study mode work |
| B07 | SQLite progress and XP | Restart preserves state; replay cannot duplicate awards |
| B08 | Build acknowledgments and journal | Self-report label is accurate; journal saves and reopens |
| B09 | Demo chatbot and disconnected tutor | Demo replies labeled; no provider request made |
| B10 | Accessibility and responsive checks | Primary flows work on keyboard, phone width, and reduced motion |

Recommended first working slice: B01–B04 for L01, then B05–B08 for L01, then render L02–L06 from the same content-driven components. Add B09 and B10 before closing M1.

## M2: Google and first live reply

| ID | Task | Done when |
| --- | --- | --- |
| B11 | Provider/config interface | Explicit demo/Cloud modes; secret-free status API |
| B12 | Actual credential-mode setup | User's express key or standard Cloud auth initialized correctly |
| B13 | Bounded connection check | One short real request verifies connectivity; failure redacted |
| B14 | Lesson-aware tutor | Current objective/excerpt sent; tutor and chatbot histories separate |
| B15 | Basic real chatbot | A user message gets a complete real reply; empty/blocked/timeout handled |
| B16 | Limits and usage | Input/concurrency/request limits enforced; usage labeled accurately |
| B17 | Author L07–L09 | Validated complete lessons with real app tasks and expected behavior |

M2 uses independent single-turn tutor/chat requests. Earlier display history is isolated by purpose and lesson; saved conversations and selected context are M3. Fake-provider and SDK transport tests verify mechanics only. See [M2 verification](M2_VALIDATION.md).

## M3–M7

| ID | Stage | Task and gate |
| --- | --- | --- |
| B18 | M3 | Chats and personas persist; follow-up recall verified |
| B19 | M3 | Streaming/stop/retry; partial state survives refresh; alternate responses selected explicitly |
| B20 | M3 | Context inspector; bounded valid message history; author L10–L12 |
| B21 | M4 | Similarity and attention toys; author L13–L15 with analogy limits |
| B22 | M5 | Curated notes and chunk IDs; keyword baseline before optional embedding calls |
| B23 | M5 | Grounded answers and checked source IDs; unsupported question test; author L16–L18 |
| B24 | M6 | Typed allowlisted tool; injection fixtures; no generated-code execution |
| B25 | M6 | Repeatable evaluation set and report; author L19–L21 |
| B26 | M7 | Usage budget, export, backup and restore; author L22–L24 |
| B27 | M7 | Capstone and full local acceptance checklist |

## Later content-editing workspace

Draft schema-constrained updates, show a before/after preview, validate prerequisites and code, publish atomically, preserve IDs/progress, and restore snapshots. Keep this separate from Ask AI. Implement only after the learner requests in-app editing; development prompts already support local course updates.

## Risks and concrete responses

| Risk | Response |
| --- | --- |
| Too much frontend learning at once | Templates and small JS; introduce one browser concept per task |
| Games feel unrelated to building | Every lesson names the corresponding chatbot behavior |
| Toy model taught as real LLM architecture | Visible analogy limits and explicit toy labels |
| AI gives a misleading explanation | Authored content and answer keys remain primary; tutor can be reported |
| Credential mode mismatched | Explicit auth mode and a real connection smoke test |
| Usage or cost surprises | Local request/token limits, explicit calls, configurable verified prices |
| Updated course loses progress | Stable IDs, version snapshots, immutable awards, rollback manifests |
| Public deployment exposes app state | Local-first; hosting only after access control and durable storage work |

## Completion report template

Milestone; working features; learner ownership task; evidence/checks; unresolved issues; next lesson; next build task. Replace planned statuses only when implementation and verification justify it.
