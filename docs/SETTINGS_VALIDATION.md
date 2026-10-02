# Settings connection update · 2 October 2026

The connection form replaces Google environment configuration. It saves a Cloud express key, model, enable/disable preference, or Standard Cloud ADC fields without restarting the app. Save and Remove make no Google calls; Test is separate and may incur charges. A blank key keeps the current credential, and removing it disables AI without deleting learning/chat data.

The key is encrypted by Windows user-scope DPAPI in ignored `data/ai-settings.json`. Settings/status responses return only `key_saved` and nonsecret connection fields. Password input clears after successful save or page exit; it is never put in browser draft storage. Failed saves keep the previous connection. Unreadable storage opens offline with a recovery notice. Other operating systems do not receive a plaintext fallback. Processes running as the same Windows account remain inside this local app's trust boundary.

Backend checks cover encrypted persistence, real DPAPI round-trip, process restart, blank-key retention, replacement/removal, hot adapter update, disabled state, ADC fields, invalid input and redaction, cross-origin rejection, corrupt storage, atomic-write failure, and active-request rejection. Existing provider, chat, progress, and numeric tests run alongside them.

All 118 tests passed in the full-suite run; the two subsequently added atomic-write/admission regressions also pass, making 120 verified tests in total. Two existing upstream deprecation warnings remain. The content verifier passes all 15 Python examples and 90 rounds. The separate fake-provider tutor/chat browser regression also passes.

`tools/browser_settings_check.py` uses an isolated database and an explicit FAKE provider. It checks saving without a reload/restart, failed-save retry, empty password after Save/reload, no key in public responses or browser storage, disabled/enabled states, a fake connection test and chat, ADC field switching, Remove key, keyboard focus, and layouts at 360/390/768/1280/1440px. No external requests or JavaScript errors occur. Its screenshot/report are ignored under `data/qa/`. This proves UI and transport mechanics, not live Google permissions.

L09 version 2 changes setup text and one hint only. Its game/quiz/build IDs, answer keys, Python example, and scoring rules are unchanged. Other lesson files are unchanged; the pre-update snapshot is retained under `data/backups/before-settings-ui/`. Existing completed work and XP remain valid.

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tools/verify_docs.py
.\.venv\Scripts\python.exe tools/browser_settings_check.py
```

Actual Google access still requires the learner's own credential, supported model, and successful Test connection. No real credential is used in these checks.

The learner app was restarted on loopback port 8001. Direct checks confirm the new password form and secret-free status endpoint; all learner SQLite tables match their pre-restart hashes. The screenshot comes from the isolated fake-provider profile.
