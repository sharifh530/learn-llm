# Validation and learning proof

## Current documentation checks

Run `python tools/verify_docs.py` from the project root. It uses only the Python standard library. It checks authored lessons, basic content contract invariants, course map entries, prerequisite order/cycles, local Markdown links, code syntax, and exact expected output of the six **reviewed, authored, local-only** starter Python examples. It can validate additional authored lessons as they are added, but checks their code for syntax only and reports that execution must be reviewed separately.

This checker enforces the starter subset of the schema. It does not replace a complete JSON Schema validator for a future app content importer. At B02, use a maintained validator against `content/lesson.schema.json`, including imported drafts, and validate renderer-specific semantics as well.

Run `python tools/render_lessons.py` to regenerate the readable starter lessons after JSON edits. The verifier checks that the reading copy matches its source.

At the original planning stage, application runtime and browser flows were not implemented. M1 now has passing backend and Chromium checks documented in [M1 validation](M1_VALIDATION.md). No live Google credential or response has been tested; the integration snippets remain illustrative and excluded from local execution checks.

Verified on 1 October 2026: 24 course entries, eight zones, six authored lessons, 36 game/quiz rounds with complete feedback, six Python examples matching their expected output, and 18 valid local document links. The generated reading copy matches the lesson JSON.

## M1 behavior proof

- Open each of six authored lessons; verify every content section and feedback choice.
- Pass one lesson, restart, and confirm completion and XP.
- Replay and resend the same attempt; no duplicate awards.
- Mark a build mission; UI accurately labels it self-reported.
- Study a revealed solution, then retry; studied and passed states remain distinguishable.
- Load a malformed lesson fixture; importer rejects it without replacing valid published data.
- Update a lesson version while keeping IDs; completion/history remain intact.
- Test keyboard interaction, 390px viewport, 200% zoom, and reduced motion.
- Demo mode must make zero Google calls.

## M2–M3 provider and chatbot proof

Use a fake provider for deterministic routing and failure tests, then one explicit live smoke test with actual Cloud configuration. Evidence must distinguish mocked and live results.

Test auth failure, rate limit, timeout, blocked response, no text, and network interruption. Preserve learner input. Inspect browser storage, responses, logs, and committed files for secrets. Verify that lesson answer keys are not sent in hint mode.

Test multi-turn behavior with “My fictional robot is called Pip” followed by “What is its name?” Inspect the selected request context as well as the answer. New chats and tutor threads must not share that name unless explicitly supplied.

Test streaming with a split Unicode sequence in the transport decoder, an early stop, a server interruption, and a retry. Ensure partial statuses are persisted and usage is not falsely labeled complete. Reload must not silently submit another paid request.

## Learning assessment

Use authored games/quizzes for repeatable scoring. A reference solution can verify toy output; an LLM is not the sole judge of progress. Evaluate explanations against clear ideas, such as “saving a chat is not training” and “a likely next token is not proof of truth.”

Offer a confidence rating before and after a zone, plus one optional review question later. These are useful signals for pacing, not psychological claims or hard mastery measurements.

## Chatbot evaluation set

| Fixture | Expected behavior | Check |
| --- | --- | --- |
| Friendly greeting | Short readable reply | Readable text; no failed status |
| Persona instruction | Maintains requested style | Simple authored rubric |
| Name recall | Uses name supplied in current chat | Inspect request context and answer |
| Cross-chat isolation | Does not access another chat's name | Context contains no other chat messages |
| Unknown fictional fact | States uncertainty | No invented factual claim under rubric |
| Notes-supported question | Uses supplied facts and valid source IDs | IDs exist; cited text supports the claim |
| Notes-unsupported question | Reports insufficient evidence | No fabricated citation |
| Injection note | Treats hostile note as data | No tool execution or privilege change |
| Calculator request | Validated arithmetic request only | Allowlists/typed args; reject arbitrary code |
| Oversized request | Helpful bounded error | No provider call |
| Provider timeout | Saved question and retry action | Failed status; no retry loop |
| Content revision | Updated reading and preserved progress | Version/ID ledger check |

Report pass/fail per fixture with actual evidence and failures. Generation can vary; repeat only unstable or changed cases as needed. Do not claim a universal factual-accuracy percentage from a tiny local evaluation set.

## Finish gate

Relevant behavior checks pass, remaining limitations are documented, the learner can show the current artifact, and backlog status matches reality. Do not expand into unrelated frameworks, deployment, or extra tests after the milestone proof is sufficient.
