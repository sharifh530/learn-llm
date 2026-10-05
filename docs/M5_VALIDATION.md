# M5 verification

M5 adds a curated Knowledge Library, transparent keyword retrieval, temporary
chunk preview, exact source checks, and authored L16–L18. There are now 18
lessons, 108 game/quiz rounds, and 18 runnable standard-library Python examples.
Final checks were completed on 5 October 2026.

## Evidence

- The full backend suite passed **147 tests**, with the two existing upstream
  deprecation warnings. Library coverage includes missing evidence, restricted
  note filters, negation exposed as a keyword match, bounded inputs, quote/ID
  checks, failed-output usage retention, truncation, global quota, cache recovery,
  cloud instance changes, and atomic rejection of duplicate curated note IDs.
- Fabricated references, non-retrieved IDs, altered prices, duplicate citations,
  malformed shapes, and extra free-form answer fields are withheld. Invalid
  results are not cached as successes. The provider has already run, so known
  usage is retained and the failed attempt ID remains consumed.
- Successful fake Google selection recovers through the same attempt ID after
  restart and across separate cloud-mode instances. Changes to retrieved note
  content/version bind the request digest to a new context and reject ID reuse.
- The isolated Library browser check passed offline clues, uncertainty, source
  filtering, checked fake selection, source-link focus, lost-response recovery,
  rejection UI, draft preservation, safe text rendering, preview chunking,
  keyboard order, reduced motion, and 200% CSS zoom. Widths checked:
  360/390/768/1024/1440px. No JavaScript errors or external requests occurred.
- The entire browser lesson flow passed all 108 rounds and completed 18 lessons
  for 1,440 XP in its disposable fixture. Replay, study mode, journals, content
  reload, disabled tutor, dialog focus, demo/AI separation, and outline L19 passed.
- Existing cloud Settings/chat browser checks passed after the shared request
  changes. They use fake credentials and a fake provider, never real Google calls.
- All 18 reviewed lesson examples reproduce their expected output. Schema,
  prerequisites, stable IDs, feedback coverage, generated reading copy, and
  local documentation links validate.

Commands:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tools/verify_docs.py
.\.venv\Scripts\python.exe tools/browser_library_check.py
.\.venv\Scripts\python.exe tools/browser_check.py
.\.venv\Scripts\python.exe tools/browser_cloud_check.py
```

QA reports and desktop/mobile screenshots are ignored under `data/qa/`.
Production commit `25f7c97` was deployed on 5 October 2026. Vercel reported Ready
for deployment `6GH8LmWvJ2Zr3faNVUfw9ggYga5n` after 23 seconds. The signed-in
production Library returned the three mango-related quotes and the missing-owner
uncertainty response, both with zero Google calls. The proof image is
`data/qa/m5-live-library.png`. No progress or chat was created by those checks.
The existing localhost tab could not be manually inspected because the browser
security policy rejected tab access; isolated local browser proof and the live
production check are the UI evidence for this release.

The pre-M5 lesson/database snapshot is `data/backups/before-m5/`. Earlier
lesson files L01–L15 match that snapshot byte-for-byte. Every learner database
table also matched before local restart; implementation checks used disposable
databases. No schema migration, new package, or real provider call is required
by M5. Windows and cloud learner profiles remain separate.

## Limits

Software proof does not establish learner understanding or actual Google
connectivity. Fake-provider selection verifies mechanics only. No real key was
entered or tested by the implementation agent. Google's JSON format obedience
and semantic selections require a live comparison; invalid outputs fail closed.

Keyword overlap cannot understand negation or every synonym. It can retrieve
irrelevant notes or omit relevant ones, especially under a note filter or
top-three limit. The exact-quote gate does not prove relevance, completeness,
note trustworthiness, or factual correctness. No free-form model claims are
displayed. Curated notes are fictional; practice previews are not saved or
included in the library. Embeddings, file uploads, arbitrary tools, and an
in-app note editor are outside this milestone.

The header now wraps when enlarged content no longer fits. Native browser
viewport checks and 200% CSS zoom pass, but this is not comprehensive testing
across screen readers or every browser zoom implementation. Existing system
and manual reduced-motion preferences apply to new clue transitions.

Rollback the M5 code/content commit together. Preserve learner databases and
Settings. Existing lesson/activity identities and XP awards are unchanged;
records for new lessons remain available if the content is restored later.
