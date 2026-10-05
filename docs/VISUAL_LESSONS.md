# Learn by watching the Python

Updated 5 October 2026. All 18 authored lessons now have visual stories: 73 scenes and 18 short “Check your hunch” games. Course revision is 7; each lesson version advances by one (L09 is version 3; the others are version 2).

## Your first five-minute experiment

Open L05, **The probability arcade**, on the Learn tab. Read **Start with**, **Python does**, and **Look for**. These explain the values entering the example, the operation, and the result you should watch.

1. Choose **Next scene** to see the scores become probabilities at temperature 0.5. Tea has about 86.68% of the probability.
2. Advance to temperature 2. Tea still leads, but falls to about 50.65%; the alternatives grow.
3. Follow the highlighted Python lines beside the bars. The function divides scores by temperature, exponentiates, and normalizes them. It does not ask Google or generate a reply.
4. Try the hunch question, including the wrong choice to read its hint. Retries are welcome.
5. Copy the unchanged Python example and run it locally. Compare its output with the final visual console.

Use **Play story** for automatic scene changes, **Pause story** to inspect a step, or select any numbered scene. **Start over** resets the picture. Pace can be Slow (7 seconds), Steady (4.5 seconds), or Quick (2.5 seconds).

Next, try L14: the future position gets zero attention even when it has the largest score. Then L15: training loss falls while held-out loss rises. In L18, change a quoted price in the story and watch the exact-source check fail.

## What each lesson shows

| Lessons | Visible idea |
| --- | --- |
| L01–L03 | Dictionary lookup and fallback; word counts; a next-word path ending at a stop marker |
| L04–L06 | Token pieces and spaces; temperature probability bars; saved history versus selected context |
| L07–L09 | Prompt ingredients; separate system/user fields; the six labeled stages of a model request |
| L10–L12 | Complete conversation pairs; partial streaming text and Stop; human judgments of reply quality |
| L13–L15 | Vector direction and cosine; masked attention weights; training and held-out losses |
| L16–L18 | Chunk boundaries; literal keyword scores; valid, altered, and fabricated source evidence |

These are authored traces of the existing Python examples. They are not an interpreter, a real model, live billing measurements, or a security guarantee. Each story states what its simplified picture leaves out. You can expand **Read the deeper explanation** when you want more detail.

## Controls and accessibility

Motion starts only when you choose Play or navigate scenes. Playback stops at the last scene, when Learn is hidden, when the browser tab is hidden, or when motion is disabled. Manual and operating-system reduced-motion preferences disable autoplay and animated transitions; every scene remains available through the buttons.

Native buttons work from the keyboard. Scene changes announce a short status. The source pane scrolls internally to show a highlighted line without moving the page or keyboard focus. Labels, numbers, and prose carry meaning alongside color. Phone layouts stack the diagram and code. With JavaScript disabled, the first scene and full Python remain visible, followed by a reading copy of every scene.

## Authoring and key files

The optional `visual` object lives in each authoritative lesson JSON. It includes title, input/operation/output context, a simplification limit, 3–8 frames, and a small choice question. Each frame has a title, explanation, referenced Python line numbers, a registered layout, display items, and console text. Layouts are `flow`, `tokens`, `bars`, `memory`, `checks`, `chunks`, and `evidence`.

- [Content contract](CONTENT_CONTRACT.md) defines validation and revision rules.
- `app/visuals.py` checks references, finite bar amounts, final output, and the single correct hunch choice.
- `app/templates/lesson_visual.html` renders the initial story and no-JavaScript reading copy.
- `app/static/js/lesson-visual.js` switches scenes, highlights source, and manages playback.
- `app/static/css/lesson-visual.css` defines responsive diagrams and code treatment.

The content remains bounded plain data. No raw HTML, executable lesson scripts, model calls, or Python execution are introduced. Validation is part of the candidate content snapshot: a bad visual preserves the previous published content.

Existing lesson/activity IDs, games, quizzes, build missions, Python examples, answer keys, and XP rules are unchanged. The new hunch practice adds no XP and saves no attempts. Existing completion snapshots remain intact; a newer lesson revision can offer optional review.

## Verification record

- **156 backend tests passed**, including invalid visual rollback and preservation of an earlier completion across a visual revision.
- **73 scenes across all 18 lessons passed browser checks**: diagram text, line references, console output, navigation bounds, feedback, and unchanged copied source.
- All lessons passed checks at **360, 390, 768, 1024, and 1440px**. The browser proof also covers 200% CSS zoom, explicit playback/pause, bounded completion, hidden-panel cleanup, bar interpolation, system/manual reduced motion, and plain-text rendering.
- The existing **108-round lesson flow passed** with expected 1,440 XP and no browser errors. Visual-only checks recorded zero XP, journals, or AI requests.

Screenshots and the report are ignored local artifacts under `data/qa/`. The pre-change content and consistent SQLite backup are under `data/backups/before-visual-lessons/`. Checks use disposable profiles; no real Google requests were made. These checks establish software behavior, not learner comprehension or a full assistive-technology audit.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tools/verify_docs.py
.\.venv\Scripts\python.exe tools/browser_visual_check.py
.\.venv\Scripts\python.exe tools/browser_check.py
```

For rollback, restore the previous code/schema/content revision together and regenerate the reading copy. Preserve current learner databases, credentials, chats, and attempts rather than restoring old learner data over newer work.
