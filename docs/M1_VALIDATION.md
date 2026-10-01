# M1 verification record

Verified on 1 October 2026. Runtime: Windows, Python 3.14.7. Dependency versions are pinned in the requirements files and full environment lock.

## Backend

`python -m pytest -q --tb=short`: **15 passed**.

Evidence covers all six lessons' server scoring and feedback; complete/restart persistence; journal persistence; idempotent and concurrent retries; study versus passed state; malformed answers and stale versions; content/schema validation; unchanged completion/XP after content revisions; new question IDs requiring current review; safe rendering; and local request guards.

The installed Starlette test client emits a deprecation warning for its `httpx` compatibility path. The tests pass; this affects the development test dependency, not the runtime learning flows.

## Browser

`python tools/browser_check.py`: **passed in Chromium**, using its own disposable database.

- Completed all six lessons through the UI, including 36 game/quiz rounds.
- Tested wrong-answer feedback, study mode with no XP, replay without duplicate XP, and 480 total XP after six complete lessons.
- Saved a journal entry and confirmed it after reload.
- Tested keyboard tab navigation, tutor dialog open/close and focus return, and question draft preservation.
- Tested demo topic replies, honest fallback, safe display of script-like user text, and tab-scoped demo history.
- Reloaded valid content and confirmed progress preservation; outline-only lessons stay descriptive rather than appearing authored.
- Checked page widths of 390, 640, 1280, and 1440 CSS pixels with reduced motion. No horizontal page overflow, JavaScript errors, or external browser requests were recorded.

The 640px layout is a useful reflow check for a small laptop at 200% zoom; this is not a claim that all browser zoom/accessibility behavior has been audited. Formal accessibility compliance and other browser engines remain unverified.

After increasing core lesson and answer text to 16px, a focused layout check confirmed that font size and no horizontal overflow at 390, 640, and 1280px. Mobile and desktop screenshots were visually inspected.

Screenshots and the machine-readable report are in the ignored `data/qa` directory. The browser checks do not alter the learner's database or award real learner XP.

## Boundaries

Google connectivity and model replies are intentionally absent from M1. Demo responses are deterministic Python rules. Local-code missions are self-reported. Browser Python execution, accounts, public hosting, persistent AI chats, and in-app content publishing remain future milestones.
