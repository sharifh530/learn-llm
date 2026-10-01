# Studio redesign verification

Verified on 1 October 2026. This is a UI update to the existing M2 app; lesson content, provider configuration, scoring, and database behavior are unchanged.

## What changed

- Cream, sage, teal, citrus, and coral replace the earlier blue/gray theme.
- Locally served Bricolage Grotesque and DM Sans fonts, custom SVG robot and zone icons, larger reading text, and tactile controls.
- Expandable lesson contents on phones and shorter Play/Quiz covers bring questions closer to the top.
- Native browser animations for page entrances, feedback, messages, and short XP celebrations. Only decorative home illustrations loop.
- A persistent header motion toggle; system reduced motion takes priority. Disabling motion cancels active animations and removes particles.

## Automated evidence

`tools/design_check.py` launches a separate app with an isolated SQLite database and Google disabled. It checks:

- Home, lessons, games, workshop, chat, and settings at widths 360, 390, 640, 1024, and 1440 CSS pixels, with no horizontal page overflow.
- Self-hosted fonts and loaded illustrations, with no external browser requests or JavaScript errors.
- Motion preference persistence, cancellation of all active animations, and system reduced motion.
- An actual fixture reading completion produces ten XP particles, cleans them up, and produces none with reduced motion.
- Mobile lesson contents and tutor Escape/focus restoration.
- A 640×450 CSS viewport representing the reflow available from a 1280px laptop at 200% zoom. This is a reflow simulation, not an actual browser-zoom measurement.

Screenshots and a JSON report are saved under the ignored `data/design-checks/<run-id>/` directory. These test completions do not change the learner's database.

The existing learning browser check passes all nine lessons and 54 game/quiz rounds, including replay XP protection, drafts, journals, and keyboard interactions. The fake-provider AI browser check passes tutor/chat requests, error recovery, safe text rendering, and retry behavior. The backend suite has 43 passing tests; two upstream deprecation warnings remain.

## Color measurements

Calculated sRGB contrast ratios for representative implemented combinations:

| Pair | Ratio |
| --- | ---: |
| Main ink on paper | 11.69:1 |
| Muted text on cream | 5.53:1 |
| Muted text on mint | 5.07:1 |
| White on primary teal | 6.41:1 |
| Citrus label text | 5.85:1 |
| Coral label text | 5.59:1 |
| Error feedback text | 5.86:1 |
| Success feedback text | 6.37:1 |

Feedback also uses wording and symbols. Main navigation, motion, copy, tutor, and suggestion controls have minimum 44px targets. These targeted checks do not constitute a full WCAG audit.

## Reproduce

```powershell
.\.venv\Scripts\python.exe tools/design_check.py
.\.venv\Scripts\python.exe tools/browser_check.py
.\.venv\Scripts\python.exe tools/browser_ai_check.py
python tools/verify_docs.py
```

The actual local lesson was also inspected in the in-app browser. Live Google account verification remains the existing M2 credential-dependent gate; this redesign does not require Google calls.
