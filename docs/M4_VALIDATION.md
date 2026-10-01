# M4 verification

Verified 1 October 2026 with Python 3.14.7 and isolated Chromium profiles. M4 is implemented locally: three numeric experiments and L13–L15. The app now has 15 authored lessons and 90 game/quiz rounds. Live Google gates from M2/M3 remain open; M4 itself needs no provider.

## Evidence

- `pytest -q`: **105 passed**, with two existing upstream deprecation warnings (Starlette's test transport and Google SDK typing). No failed tests. Raw NaN/Infinity input is rejected with serializable field diagnostics rather than a server error.
- Backend tests cover cosine direction/zero handling; masked and unrestricted stable softmax; weighted values; inference without updates; gradient updates; held-out degradation; learning-rate oscillation; finite bounds, dimensions, strict types, operation and extra-field rejection; and atomic rejection of unknown lesson `lab` names.
- All numeric routes preserve every database table, including progress, XP, journal, chats, and Google usage. Cross-origin mutation rejection and no-store responses are checked.
- The content verifier checks 24 map entries, eight zones, 15 full lessons, 90 rounds, all answer references/feedback, prerequisites, document links, and the generated reading copy. All 15 explicitly reviewed Python examples reproduce their expected output.
- `tools/browser_labs_check.py` checks toy results, keyboard tabs and sliders, masking, predict/train separation, held-out loss, rate-1 bouncing, full-precision refresh recovery, failed local requests, corrupt optional storage, and responsive layouts at 360/390/640/1024/1440px. Reduced motion disables animations. The profile has zero learner XP and zero Google attempts, no external requests, and no JavaScript errors.
- `tools/browser_check.py` exercises all 90 rounds and completes all 15 lessons in its separate fixture, totaling 1,200 XP. It covers existing replay, study mode, journal, disabled tutor, demo rendering, content reload, and outline availability. Fixture XP is never applied to the learner's database.

Commands:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tools/verify_docs.py
.\.venv\Scripts\python.exe tools/browser_labs_check.py
.\.venv\Scripts\python.exe tools/browser_check.py
```

Local QA artifacts are ignored under `data/qa/`: `m4-browser-report.json`, `browser-report.json`, and Observatory desktop/mobile screenshots. A pre-M4 content/database backup is under `data/backups/before-m4/`; course JSON additions keep existing lesson versions, IDs, and answer keys unchanged. Database schema remains version 3.

Before restarting the learner app, L01–L12 were compared byte-for-byte with the backup. Every learner database table also matched its pre-M4 snapshot, including saved chats and journals; no learner data was changed by the implementation checks.

The final Codex in-app browser attachment timed out before a UI snapshot could be obtained. Visual acceptance and screenshots therefore come from the isolated Chromium run above. The local server was restarted on port 8001 and its M4 endpoints checked directly.

## Limits

These checks establish software behavior, not a learner's understanding. Build acknowledgments are self-reported. Fruit features are authored ratings, not learned embeddings. Attention scores/values are manual, not a model's attention or reasoning. One-weight training changes no hosted model and has no language ability. Its single held-out example is not a complete evaluation dataset. Native meters and loss plots also have numeric text/table alternatives; broader assistive-technology testing remains outside these checks.
