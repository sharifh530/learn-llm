# Decision record

| Decision | Status | Reason |
| --- | --- | --- |
| Google Cloud / Vertex AI provider | Confirmed by learner | Matches user's selected account/API source |
| Small ChatGPT-style app around a pretrained model | Planned core | Achievable useful chatbot; teaches application construction |
| Tiny local prediction models as learning toys | Planned core | Exposes learning/prediction without GPUs or complex libraries |
| Single learner, local first | Planning assumption | Small reversible starting point; no account/deployment burden |
| FastAPI + Jinja + native CSS + small JS | Proposed implementation | Python stays central; reduces simultaneous frameworks |
| SQLite progress/chats and JSON content | Proposed implementation | Simple persistence and prompt-friendly lesson updates |
| Six full starter lessons and 24 total path entries | Authored plan | Usable starting content with manageable later expansion |
| Offline games and local scoring | Planned core | Learn without credentials; deterministic feedback |
| Separate tutor and chatbot conversations | Planned core | Prevents tutoring context leaking into experiments |
| Credentials from server environment | Planned core | Avoids reusable secrets in browser code/storage |
| In-app generated lesson publishing | Deferred | Local development prompts support updates immediately |
| Browser Python execution | Deferred | Requires isolated runtime and its own resource/security design |

## Information needed at implementation time

- Actual Cloud credential mode: express key, standard key, or ADC; no secret content needed in chat.
- Supported model/location and current project access.
- Installed Python compatibility with pinned dependencies.
- Whether the app will eventually stay private or be hosted for other learners.

These do not block planning or M1. Auth details become necessary at M2; hosting decisions become necessary only before deployment. Working name, color palette, and examples can be revised at any time through a prompt.

## Existing workspace

This project lives in its own `llm-playground` directory. The separate `youtube-reel-maker` project is unrelated to this plan.
