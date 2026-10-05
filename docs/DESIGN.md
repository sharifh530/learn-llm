# Experience and visual direction

## Direction

A playful science workshop for an adult Python learner. The interface should feel like a notebook and experiment bench: clear reading space, vivid interactive experiments, and encouraging feedback. Avoid a dense dashboard or a long marketing page.

Working identity: **Tiny Chat Lab**. Pip is now a custom SVG robot used in the home experiment, brand, lesson encouragement, and chatbot. Only decorative home pieces float; lesson text and inputs stay still.

## Visual foundation

- Warm cream canvas `#F6F5EC`, paper `#FFFEF9`, deep green ink `#183E35`. Sage surfaces give the lab a consistent visual texture.
- Primary action `#176B57` with white text. Citrus `#F4D66E` highlights experiments and XP; coral `#EEA18B` highlights the tutor and illustrated zones. Pale mint, apricot, and citrus distinguish objectives, predictions, and feedback.
- Success and error colors appear with text and icons, never as the only signal.
- Self-hosted Bricolage Grotesque for display text and DM Sans for reading; system monospace for Python. Font files and SIL Open Font licenses are included under `app/static/fonts/`, with no external browser font request.
- Body at least 16px, line-height about 1.6, reading width about 65 characters.
- Corner scale: 20–26px main surfaces, 13–17px inputs and feedback, tighter 8px labels. Tinted lower-edge shadows make controls feel tactile. Use surfaces for actual interactive grouping.
- Spacing based on an 8px rhythm. Clear whitespace between concept, experiment, and explanation.

Verify actual contrast in the implemented combinations, including muted text, disabled states, and focus indicators. Target WCAG AA behavior, but do not claim compliance until checked.

## Screen composition

### Home

Top: brand, Learn, Build, My Chatbot, Settings. Main: “Ready for your next experiment?” and one large Continue action. Below: eight zones in an ordered learning path; eighteen authored lessons are available, future zones have descriptive outlines. A small workshop summary shows which chatbot features already work.

No invented achievements or usage numbers. The first-time state says “Your first experiment is ready.”

### Lesson

Desktop: compact zone navigation; centered reading column; optional Ask AI drawer. Keep content and tutor width independently readable. Tablet/mobile: one reading column, collapsible contents, tutor as a panel with an explicit return-to-lesson button.

The game is the visual center of each lesson: word choices, a probability distribution, or a context backpack. Explanations follow the learner's action rather than revealing everything at once.

### Workshop and chatbot

Workshop pairs the current feature with a small mission. Chatbot uses a familiar composer and message thread, with a visible Demo / Connected state. The context inspector is optional and explains which messages the app sends; it does not display or invent private model reasoning.

## Interaction rules

- A selection changes styling immediately and shows a textual selected state.
- Submit reveals authored feedback; correct/wrong results use both wording and visual cues.
- Celebrations last under a second and only occur after meaningful completion.
- Honor `prefers-reduced-motion`; remove particles, page entrances, and decorative movement. A persistent header motion control can also disable motion manually. System reduced motion takes priority.
- Keyboard focus remains visible and predictable; closing the tutor returns focus to its trigger.
- Touch targets aim for at least 44px. No hover-only answer explanations.
- Streaming announces updates at sensible intervals through an accessible status region, not every token.
- Preserve a drafted question when a panel closes or a network request fails.

## Voice and example copy

Wrong answer: “Good experiment. This answer mixes up chat history and training. Saving a message changes the app's record; it does not update the model's weights.”

Completion: “You built your first predictor. Try changing its example and predict what happens next.”

Disconnected tutor: “Ask AI will be available after Google is connected. The lesson, game, and solution still work.”

Progress update: “This lesson has a clearer example now. Your completion is saved; review it whenever you want.”

## Design proof before release

Check a small laptop, a 390px-wide phone, keyboard-only use, browser zoom at 200%, long Python lines, long AI replies, and reduced motion. Inspect first-time, loading, failed, stopped, completed, and content-updated states. Document real observations rather than assuming responsive CSS guarantees usability.


## Implemented studio redesign, 1 October 2026

The existing FastAPI/Jinja/native CSS stack is preserved. `studio.css` extends the functional layout with the studio palette, self-hosted fonts, custom zone icons, Pip illustration, tactile controls, and larger reading text. `motion.js` uses Web Animations and IntersectionObserver for page/section entrances, tab/feedback/message transitions, and 750ms XP particles. It never initially hides content and never changes scrolling or focus. No animation library is needed.

On phones the lesson contents are expandable. Play and Quiz use a shorter lesson cover so the question appears sooner. Existing scoring, progress, and AI request behavior are preserved.

Font sources: [Bricolage Grotesque](https://github.com/google/fonts/tree/main/ofl/bricolagegrotesque), [DM Sans](https://github.com/google/fonts/tree/main/ofl/dmsans). The custom SVG illustrations and icons are native project assets.

See [UI verification](UI_VALIDATION.md) for measured checks and limits.

## Model Observatory · M4

A citrus orbital illustration introduces three keyboard-accessible experiment tabs. Sage controls sit beside live numeric results. Fruit ranking has numeric cosine values and meters; zero vectors explicitly have no direction. Attention rows pair weights with visible mask labels. Training shows separate sage training and apricot held-out losses, with solid/dashed chart lines and an exact-value table. No learner achievements or provider outputs are invented.

Phone layouts stack controls and results. Inputs and explanations remain still; entrance and tab motion use the existing system/user preference. The page links from Build and authored L13–L15.

## Knowledge Library · M5

The Library extends the existing science workshop as a café clue desk. A sage
source catalog sits beside a paper question workspace, citrus example prompts,
an inspectable search trace, and source quotes with working reference links.
The source catalog collapses into note details; on phones the question desk
appears first. The draft stays available through request failures and reloads.
Offline and Google modes remain explicit, with no automatic model calls.

Use the existing fonts, palette, Pip illustration, focus treatment, and native
stack. Brief calibration: moderate layout variation (6/10), restrained motion
(3/10), and medium information density (5/10). New clue entrances last 300ms;
question text, controls, and reading content stay still. Manual/system reduced
motion removes clue transitions. The shared header wraps when enlarged content
no longer fits, preserving usable navigation at 200% CSS zoom.

The isolated browser proof covers 360–1440px, keyboard focus, source-link focus,
errors, missing evidence, recovery, safe text rendering, and reduced motion.
See [M5 verification](M5_VALIDATION.md) for measured checks and their limits.

## Visual teaching stories

The Learn page begins with input, operation, and output context, then a sage-and-citrus visual workspace beside the matching Python. Chips show token boundaries, bars show numeric quantities, memory rows distinguish saved and selected text, and labeled checks explain source validation. The current scene controls the source highlight and its console trace; each picture explains an operation rather than decorating the page. Goals, guesses, and deeper prose remain expandable around the story.

Brief calibration: layout variation 6/10, learner-controlled motion 6/10, density 5/10. Scene tiles enter over 380ms; probability bars interpolate over 650ms. Text remains still after a scene settles. Playback is explicit, pausable, bounded, and respects system/manual reduced motion. Phones stack diagram and source. The code pane follows the selected line without moving page focus. See [Visual lessons](VISUAL_LESSONS.md) for all-scene responsive and motion proof.
