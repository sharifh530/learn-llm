# M2 verification record

Checked: 1 October 2026, Windows, Python 3.14.7.

**Software implemented and local checks passed. Live Google access is not verified.** No project credentials, model, or `.env` were present during this build. The real connection gate remains open; M2 is not fully complete until the actual account responds.

## Evidence

- 43 backend tests passed: existing progress/content guards, all nine lessons, provider policy, current-lesson selection, hint/solution context, tutor/chat separation, stale versions, secret redaction, input validation, minute/day/concurrency limits, idempotency, durable usage including failed replies with metadata, and append-only schema upgrade.
- Google SDK 2.26.0 exercised with HTTPX MockTransport: actual request serialization for Cloud count/generate, system instruction, output limit, 30-second per-call timeout, no automatic retries, input overflow, empty/blocked/unblocked responses, quota, timeout, truncation, and absent usage metadata. ADC initialization explicitly passes credentials/project/location. These are simulated transport checks, not real access proof.
- Nine reviewed offline Python examples executed in isolated subprocesses and matched expected output. The content contract validates 24 map entries, eight zones, nine authored lessons, 54 scored game/quiz rounds, feedback coverage, IDs, prerequisites, generated reading copy, and local document links.
- Chromium completed all nine lessons and 54 game/quiz rounds in an isolated database. The fixture earned 720 XP, and replay preserved it. Test build acknowledgments are fixture actions; they do not claim that the learner completed L09’s real-call mission.
- Browser checks covered keyboard tabs, dialog focus, reduced motion, journal reload, content reload, safe rendered text, outline availability, preserved disconnected AI drafts, and separate Demo/Google displays at widths 390, 640, 1280, and 1440. No JavaScript errors or external browser requests.
- A separate explicit FAKE-provider server exercised successful connection/tutor/chat UX, lesson draft isolation, preserved failure input, absent credentials in browser HTML/storage, no AI XP, and a lost response followed by refresh/retry with the same ID and no additional provider attempt. Tutor layout checked at 390, 640, and 1280 widths. No JavaScript errors or external browser requests.
- Screenshots and reports are local ignored artifacts under `data/qa` and `data/browser-checks`. Mobile tutor contents scroll inside the dialog.
- The learner database was backed up locally before upgrade. A hash comparison confirmed all existing progress, acknowledgment, activity, attempt, XP, and journal rows stayed identical while schema version changed from 1 to 2. The restarted local app reports M2 and keeps AI disabled until configured.

## Reproduce

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tools/verify_docs.py
.\.venv\Scripts\python.exe tools/browser_check.py
.\.venv\Scripts\python.exe tools/browser_ai_check.py
```

The browser scripts use isolated databases and disable real Google calls. The FAKE factory refuses a database outside `data/browser-checks`.

## Remaining gate

Configure an express Cloud key or standard project ADC locally, select a supported text model/location, restart, and run one real Settings connection test. Then verify an actual chatbot reply and lesson-aware tutor reply, record returned usage and any missing metadata, and complete L09’s real-call mission. Credential permissions, live model behavior, latency, and real billing cannot be proven by mocks.

Upstream dependencies emit two deprecation warnings in tests (Starlette HTTPX and the SDK’s Python typing alias); they do not fail these checks. Public hosting, multiple learners/workers, streaming, persistent chat recall, currency budgets, and provider-quality evaluation remain later work.
