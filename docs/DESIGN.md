# Experience and visual direction

## Direction

A playful science workshop for an adult Python learner. The interface should feel like a notebook and experiment bench: clear reading space, vivid interactive experiments, and encouraging feedback. Avoid a dense dashboard or a long marketing page.

Working identity: **Tiny Chat Lab**. Optional mascot: Pip, a small curious robot used beside hints and achievements, never as a competing animation during reading. A mascot illustration is a future asset, not required for the first build.

## Visual foundation

- Light canvas `#F7F9FC`, white reading surface, dark ink `#182235`.
- Primary action `#174CC9` with white text; lighter blue reserved for selection backgrounds.
- Success and error colors appear with text and icons, never as the only signal.
- System sans-serif text with a readable system monospace for Python. No external font dependency initially.
- Body at least 16px, line-height about 1.6, reading width about 65 characters.
- Consistent corner scale: 12px panels, 8px inputs, 10px buttons. Use surfaces for actual interactive grouping.
- Spacing based on an 8px rhythm. Clear whitespace between concept, experiment, and explanation.

Verify actual contrast in the implemented combinations, including muted text, disabled states, and focus indicators. Target WCAG AA behavior, but do not claim compliance until checked.

## Screen composition

### Home

Top: brand, Learn, Build, My Chatbot, Settings. Main: “Ready for your next experiment?” and one large Continue action. Below: eight zones in an ordered learning path; six authored lessons are available, future zones have descriptive outlines. A small workshop summary shows which chatbot features already work.

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
- Honor `prefers-reduced-motion`; remove confetti and nonessential movement.
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
