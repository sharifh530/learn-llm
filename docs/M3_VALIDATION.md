# M3 verification and limits

M3 software is implemented and verified locally. Live Google multi-turn recall, streaming, and cancellation still require actual credentials and model access; no live account call was made during this implementation. M2's existing real-account gate remains open.

## Evidence

- Twelve authored lessons, 72 game/quiz rounds, and twelve offline Python examples pass content validation. L10–L12 cover context, streaming, and evaluation.
- 65 backend tests pass (two upstream deprecation warnings). They verify persistence across an app restart, selected role ordering, persona instructions, request-ID replay/conflict, shared single-turn/stream concurrency limits, Stop fencing, partial selection, variants, archive/restore, context budgets, terminal statuses, output-size limits, reported/unknown usage, missing stream completion markers, and restart recovery without generation.
- Actual pinned Google SDK serialization is tested using HTTPX MockTransport: `countTokens` followed by `streamGenerateContent`, user/model/user roles, output limits, usage, blocked/empty/output-limited responses, and exclusion of thought parts. This is transport proof, not live connectivity.
- The complete learning browser flow passes twelve lessons and 72 rounds with fixture XP 960. Replay doesn't increase it; drafts, journals, keyboard navigation, content reload, disabled Google, and responsive layouts pass.
- The existing fake-provider browser flow passes connection/tutor separation, safe text, Google/Demo isolation, failure drafts, and a lost accepted POST response recovered with the same ID and no extra attempt.
- `tools/browser_chat_check.py` passes saved personas and messages, follow-up context, explicit alternative selection, stopped partial persistence, explicit partial inclusion, refresh during a running reply without another attempt, failure/retry variants, archive/restore, long Unicode context, widths 360/390/640/1440, and zero AI XP. It makes eight explicitly FAKE generation attempts, with no live Google calls.

Browser checks use isolated databases and reject external browser requests. Screenshots/reports are in ignored `data/browser-checks/` directories. Existing reduced-motion behavior is preserved; targeted design checks cover the shared UI.

## Persistence and recovery

Schema version 3 appends `chats`, `chat_turns`, and `generations`. Earlier progress, XP awards, journals, and AI ledger rows are preserved. A pre-update SQLite backup is stored locally at `data/backups/before-m3.sqlite3` and is not committed. After restarting the actual app, sorted-row SHA-256 comparisons confirmed that all seven existing tables were identical across schema 2 → 3. The local report is `data/backups/m3-migration-report.json`.

User messages and generation reservations commit before the worker starts. Every accepted text update is saved. Stop commits stopped status immediately; conditional writes prevent late text from overriding it. Restart marks previously running generations interrupted without another provider call. A browser disconnect leaves the worker running; reading its saved snapshots is lossless recovery.

Context includes selected whole recent turns from one chat, the persona, and the current question. Unselected partial replies are excluded. Blocked text is cleared and cannot be selected. Output-limited text is marked truncated and requires explicit partial selection. Existing selections are preserved when a new variant completes. Only the latest turn can be retried or reselected; this version does not implement a conversation branch tree.

## Limits

- One local server process; no multi-worker, authenticated, or public hosting support.
- At most 200 local chats, 100 turns per chat, five variants per turn, ten selected recent pairs, 4,000 input characters, 16,000 saved output characters, and a 90-second worker time limit checked between network operations. The SDK's read timeout is 30 seconds.
- Selection uses a labeled UTF-8 byte heuristic. Actual Google input is counted before generation. The input cap is 12,000 tokens; output cap is 2,048. No automatic summarization or retrieval is implemented.
- All live attempts share the existing eight/minute, fifty/UTC-day reservation and single-running-AI limit. Cancellation holds that reservation until the upstream worker unwinds, avoiding overlapping live work.
- Missing or failed usage is unknown, not free. Cost remains unknown; request/token limits are not a spending guarantee. Stop cannot undo upstream work or guarantee immediate billing cancellation.
- Personas are predefined styles saved per chat. Changes affect future requests; historical context snapshots remain unchanged. Demo labels persona selection but its response uses fixed Python rules.
- Unsent drafts and active-chat selection are browser-tab preferences. Saved messages, titles, personas, variants, and statuses live in SQLite. M2's old tab-only display history is not automatically imported or erased.
- Tutor requests remain separate single-turn lesson calls. No generated code execution, private model reasoning, or automatic course editing is added.

## Reproduce

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tools/verify_docs.py
.\.venv\Scripts\python.exe tools/browser_check.py
.\.venv\Scripts\python.exe tools/browser_ai_check.py
.\.venv\Scripts\python.exe tools/browser_chat_check.py
.\.venv\Scripts\python.exe tools/design_check.py
```

Real-account acceptance: configure Google using the M2 walkthrough, send a fact such as a preferred fruit, verify a live follow-up and its context snapshot, refresh/restart to verify the saved chat, stop a longer live reply, and record its real status and reported/unknown usage. Until this is performed, report software verification separately from live Google verification.
