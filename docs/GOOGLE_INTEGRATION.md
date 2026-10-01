# Google Cloud / Vertex AI integration

Selected by the learner: **Google Cloud / Vertex AI**, not AI Studio. Implemented in M2 with `google-genai==2.26.0`. Reference check: 1 October 2026. Google's current docs use Gemini Enterprise Agent Platform; the pinned SDK accepts `vertexai=True` as a legacy Cloud selector. Actual access remains unverified until credentials are configured and a real request succeeds.

## Implemented authentication

| Mode | Server configuration | Client initialization |
| --- | --- | --- |
| Cloud express key | GOOGLE_AUTH_MODE=express_key; GOOGLE_CLOUD_API_KEY; GOOGLE_MODEL | `genai.Client(vertexai=True, api_key=...)` |
| Standard Cloud ADC | GOOGLE_AUTH_MODE=adc; GOOGLE_CLOUD_PROJECT; GOOGLE_CLOUD_LOCATION; GOOGLE_MODEL; local ADC | `genai.Client(vertexai=True, credentials=..., project=..., location=...)` |
| Standard Cloud API key | Not implemented | Use ADC for a standard project, or a Cloud express key in express mode |

Both routes require `AI_PROVIDER=google_cloud` and `AI_ENABLED=true`. Copy `.env.example` to ignored `.env`, edit locally, and restart. OS settings override the file. Required-field presence means configured; only a real usable reply verifies access. Missing/disabled settings make no provider calls. The key never enters prompt context or browser storage. Do not infer a key's product from its prefix or silently reinterpret it as AI Studio authentication.

The ADC route obtains credentials through `google.auth.default` and explicitly passes them, preventing ambient GOOGLE_API_KEY from changing auth mode. Local ADC normally uses `gcloud auth application-default login`; project API, billing, IAM, and model/location access must also be correct. See [Google's Cloud setup](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/start) and [express mode guide](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/start/express-mode/overview).

## Transport and lifecycle

`app/providers.py` owns a synchronous SDK client in a context manager. FastAPI's synchronous routes run in a worker pool. The adapter selects API v1, a 30,000-millisecond timeout per call, and `HttpRetryOptions(attempts=1)` (no retries). Normally each generation attempt calls count_tokens, checks the input limit, then calls generate_content. Express mode exposes both methods. See [the SDK](https://googleapis.github.io/python-genai/) and [express REST methods](https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/express-mode/api-reference).

No network call occurs on page load or status inspection. The Settings test sends one short prompt with a 128-token configured output limit; charges may apply. Chat/tutor calls only happen on explicit submission. Clients close after each attempt. Authentication discovery/refresh may make additional auth-service requests; usage counts here refer to attempted model API methods, not every HTTP request.

SDK failures are mapped into short app messages. Raw exception strings, URLs, headers, and credentials are not returned or logged by our adapter. Auth/permissions, invalid model/location, quota, timeouts, blocked responses, and empty output remain visible failures. There is no silent demo fallback.

## Tutor context

Python selects the current known lesson and rejects stale versions. It sends objectives, explanation, analogy limit, Python example, tutor guidance, and build instructions/hints. Hint/explain modes exclude the build reference solution; solution mode explicitly includes it. Neither mode sends official game/quiz answer keys, unrelated chats, journals, or secrets. Model guidance cannot guarantee hint-only behavior; official XP is enforced separately by the progress service.

M2 requests are independent. Tutor drafts are scoped per lesson; Demo and Google display histories are separate in sessionStorage. The provider never receives earlier displayed replies. Selected history, durable chats, and streaming remain M3.

## Limits, usage, and retries

- One active AI attempt across the local app; eight new attempts/minute and 50/UTC day.
- Maximum message 4,000 characters. Actual counted input limit: 6,000 tutor / 12,000 chat tokens.
- Configured output limits: 1,024 tutor / 2,048 chat / 128 test tokens. Model compatibility must be checked with the chosen project model.
- No automatic retry. User-triggered new attempts may incur additional charges.
- A durable SQLite request ledger reserves attempts before network work, records methods attempted, reported token counts, cached successful answers, and redacted failure codes. Missing usage is unknown. Cost is unknown; no pricing assumption or spending guarantee is made.
- Lost browser responses preserve the attempt ID across refresh. Repeating the unchanged request can recover its cached answer without another provider call. Server-reported failures consume their ID; explicit retry uses a new one. Crashed running attempts become interrupted and are not silently regenerated.

This single-learner app supports one server process. Do not use multiple workers against the same ledger: startup recovery and generation admission are designed for one local instance. Currency budgets and multi-user hosting are later work.

## Verification status

Fake-provider policy checks, actual SDK serialization via HTTPX MockTransport, and an explicit FAKE-provider browser server pass. They prove mechanics only. Actual Cloud credential permissions, model behavior, latency, token reporting, and billing remain pending a real connection test. See [M2 verification](M2_VALIDATION.md) and [the setup/teaching walkthrough](M2_WALKTHROUGH.md).

When Google reports MAX_TOKENS, the UI labels the answer as potentially incomplete. Returned usage on empty/blocked replies is retained; absent metadata remains unknown. No automatic continuation is sent.
