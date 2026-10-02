# Product requirements

## Learner and promise

For a curious learner who knows basic Python and wants to understand LLMs while building a chatbot. Promise: “One idea, one game, one thing you build.” Keep tone friendly and adult; avoid treating the learner like a child.

## Primary experiences

### Home and learning map

Show a Continue action, the current build milestone, eight named zones, and recently earned achievements. Every lesson exposes its title, estimated minutes, availability, and completion state. Completed lessons remain replayable. Locked recommendations explain their prerequisites and allow browsing; outline-only content cannot be opened as if authored.

The progress display measures completed learning activities, not time spent or API usage. A low-cost / no-key mode is always apparent.

### Lesson reader

Sections: goal, prediction, explanation, analogy limit, Python example, game, quiz, build mission, reflection. Desktop can use a main reading pane and optional tutor drawer. Mobile uses one column; opening the tutor keeps the current lesson position. Buttons must work with keyboard input.

The code panel shows language, copy action, expected output, and explanation. It says “Run locally in Python” until a later isolated execution feature exists. An answer reveal is explicit and never hidden behind API access.

### Games and quiz

M1 uses a shared choice-round renderer for six games. A round has a prompt, choices, a correct choice, and feedback for every choice. Errors give a useful explanation and allow another attempt. Games do not use a timer by default.

Later game mechanics include token packing, probability sliders, message ordering, vector sorting, retrieval ranking, and instruction-versus-data classification. Every visual mechanic gets a text alternative.

Score results locally against authored answer keys. AI feedback is supplementary. Award completion XP once per stable activity ID. Replay can improve best score but cannot farm XP.

Vary displayed choice order while preserving stable choice IDs. The visible numbering is presentation, not answer identity; do not teach learners that the first option is always correct.

### Build workshop

Show “Your chatbot currently has…” and “Add this next…” with a small task, file/function target once code exists, expected behavior, and a reference solution. Save a journal entry: what I changed, what happened, what I still do not understand.

Starter missions can be marked “I tried it” by the learner. This is clearly a self-report, not a claim that the app verified local Python execution. Later automated checks validate observable behavior.

### Ask AI tutor

Entry points: lesson header, highlighted concept button, code example, and game result. Modes: hint, simpler example, explain code, quiz me, and open question. Show the exact context being sent in a compact review: lesson title, excerpt, question, and optionally a bounded tutor thread. Never attach all chat history automatically.

Tutor starts with an explanation appropriate for basic Python and uses one analogy at a time. When it introduces a term, define it. It can generate practice questions, but generated questions do not become official progress tests without authoring and validation.

Questions about the learning app use the tutor. Experiments with the chatbot use a separate chat screen. History, persona, and tutor context must not mix.

### My chatbot

M2: message composer and a complete non-streaming AI reply. M3: new chat, saved chats, title, bounded conversation context, persona selection, streaming, stop, retry, clear, export, and delete. Render all model output safely. A failed or stopped response has a visible status and does not pretend to be complete.

Context inspector shows which prior turns were sent and which were omitted. Changing personality starts a new chat or clearly labels the change. Regeneration creates an alternate response; only the selected response is sent in future context.

### Settings

Show provider, auth mode, model, region if relevant, connection status, demo mode, and usage limits. Settings accepts a key in a password field, saves it encrypted for the Windows account, and applies the connection immediately. A blank key keeps the saved credential; Remove key clears it and disables AI. Never return the saved key in page source or API responses. Save makes no provider call; Test connection is an explicit separate action.

Optional later local-only key entry: submit to the backend, retain only in server memory, expire on restart, and display a masked status. Persistent key vaults and multi-user key entry require a separate design.

## Progress and motivation

Per lesson: 10 XP for reading acknowledgment, 20 for passing the game, 20 for passing the quiz, 30 for self-reported build practice. Game and quiz pass at two correct rounds out of three; replay and hints are allowed. Maximum 80 XP per lesson. A zone boss can award 40 XP once after its own authored challenge exists.

Completion requires reading acknowledgment, passing game and quiz, and build practice acknowledgment. Reflection is encouraged, not graded. Store concept confidence as the learner's self-rating, separate from completion.

Badges describe a skill: “Prediction Explorer,” “Context Keeper,” “First Live Reply.” No penalties for taking a break, no public leaderboard, and no purchase-linked XP. Offer “Show answers and continue” as study mode; then record the activity as studied until a passing practice attempt.

## MVP acceptance criteria

- Learner can use all six starter lessons without a Google account.
- Each game and quiz explains wrong answers and can be replayed.
- Restarting the app preserves lesson progress and journal entries.
- Live Ask AI and a basic chatbot work after valid Vertex configuration.
- Disconnected, invalid-auth, rate-limited, empty, blocked, and timed-out states are actionable.
- Course text updates independently of UI code.
- Revising a lesson preserves history and does not multiply XP.
- Keyboard and narrow-screen flows are usable; reduced-motion settings are honored.

## Deferred

Accounts, cloud progress sync, payments, public leaderboards, autonomous agents, arbitrary file uploads, browser Python, fine-tuning jobs, and in-app course publishing are outside the first release.
