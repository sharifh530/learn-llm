# Tiny Chat Lab on Vercel

This is a private, single-learner deployment. Every visitor authorized by Vercel
shares the same progress, chats, quota, and Google connection. It is not a
multi-user service. Do not add public protection exceptions or share bypass
links while using personal data or a Google key.

## What changes in the cloud

Vercel runs FastAPI as a function. Its local files are not durable storage.
The hosted app therefore uses Turso's cloud SQLite over HTTPS, without a local
replica. The existing parameterized queries, scoring, XP ledger, and chat
tables are preserved. Windows continues to use local SQLite and Windows
DPAPI. [Vercel SQLite guidance](https://vercel.com/kb/guide/is-sqlite-supported-in-vercel).

`pyproject.toml` exports `app.vercel:app`. Database initialization is lazy:
builds need no database access. Missing storage or privacy configuration
returns a setup-required 503, never an ephemeral database fallback.
[Vercel FastAPI documentation](https://vercel.com/docs/frameworks/backend/fastapi).

Cloud chat creation saves the attempt first. Its SSE request then claims a
database worker lease and owns generation. Another instance or refreshed tab
observes the same saved snapshots; it cannot start the provider twice. Stop
uses database status across instances. Interrupted work preserves partial
text, excludes it from context, and never retries automatically. Only leases
abandoned for 150 seconds are recovered; cold starts leave active work alone.

## Provision and deploy

1. Use the existing Vercel `learn-llm` project connected to
   `sharifh530/learn-llm`, root directory `./`, framework FastAPI.
2. In Deployment Protection, keep Require Log In enabled and select
   **All Deployments**. Verify production and generated URLs require login
   from a browser without that session. No bypass secret is needed.
3. In Storage, create a dedicated **Turso** database using the free plan
   if available. The account owner must approve the marketplace/service
   agreements and account data sharing. Do not enable a paid upgrade.
   Place storage close to the Vercel function region (default `iad1`).
4. Connect it to this project. The integration supplies
   `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` as server environment variables.
   They are hosting infrastructure, not your Google key. There is no `.env`
   setup and no Google API key in the deployment configuration.
5. Add the nonsecret project variable
   `TINY_CHAT_PRIVATE_HOSTING=vercel-auth-all` after verifying step 2.
   This flag records the deployment prerequisite; it does not itself
   authenticate visitors. Vercel performs authentication before requests.
6. Deploy `main`. Open `/health` and verify `status: ok`, `storage: cloud`.
   Test a lesson, journal, demo chat, refresh, and another deployment before
   entering a real Google key. A setup screen is not a completed deployment.
7. In app Settings, enter a **Google Cloud express key** and supported model.
   Save makes no Google request. Test connection is explicit and may incur
   Google charges. Local ADC is only available in the Windows app.

The live production app is [learn-llm-pi.vercel.app](https://learn-llm-pi.vercel.app/).
Sign in with the Vercel account authorized for this project. Database quotas
and Vercel limits still apply; no paid resources or actual Google calls were
used for deployment verification.

## Credential and data boundaries

The Google key is encrypted with Fernet before storage. The encryption key is
derived from the server-only Turso bearer token with a domain-separated SHA-256
derivation; it is not stored in the database. Runtime credentials and hosting
account access are inside the trust boundary. A holder of the database token
can access both the database and encrypted settings. Rotating that token means
re-entering the Google key in Settings. Invalid ciphertext opens offline and
allows explicit replacement/removal; it never becomes plaintext storage.

`.vercelignore` excludes local databases, backups, `.env` files, credential
files, development tools, and tests. Git ignores these too. Local learning
data is not copied into the cloud automatically. This deployment starts a
separate learner profile; transferring personal progress requires a distinct
explicit migration request.

The cloud tables add `cloud_settings` and `generation_workers` without deleting
or renaming existing tables. Schema creation is idempotent and expands only.
Progress/AI transactions commit together and roll back on failure. Writes and
provider calls are not automatically retried after uncertain network outcomes.
[Turso HTTP API](https://docs.turso.tech/sdk/http/reference).

## Verification and rollback

Run `python -m pytest -q`, `python tools/verify_docs.py`, and the Settings/chat
browser checks. Cloud tests use an HTTPS protocol harness backed by isolated
SQLite and a fake provider. They verify transactions, rollback, encryption,
instance changes, duplicate worker fencing, Stop, partials, and fail-closed
setup. They do not prove real Google access or a real Turso service connection.

### Deployment verified on 2 October 2026

- Production code commit `b6a09b5`: Vercel deployment
  `CSiYLnSUN8kmoJsV8Q9wneSoYRiX`, Ready, Python 3.14.
- Dedicated Turso database `tiny-chat-lab`, Starter plan ($0/month), connected
  to Production. Marketplace agreements accepted after explicit owner approval.
- Vercel Authentication is enabled for **All Deployments**. No bypass links
  or public exceptions were created. The signed-in browser opened the app.
- Home loads all 15 authored lessons; L01's first game round gives feedback.
  Workshop and Settings render, with cloud persistence copy and express-key
  input. Google remains disabled; no key was entered or model call made.
- The live demo streamed two completed replies, remembered the mango from
  the previous message, and saved the title `Deployment check · mango demo`.
  The conversation is retained as a clearly labeled deployment example.
- Automated checks: 128 tests passed; isolated cloud browser checks passed
  with no JavaScript errors or external requests; documentation examples and
  internal links passed. The fake-provider tests cover settings encryption,
  Stop, duplicate streams, rollback, and instance changes.
- Native Turso closes autocommit streams. The adapter reinitializes each new
  stream and omits the local SQLite file-header `user_version` pragma.
  The local database keeps its version marker and remains untouched.

Verification limits: this computer's standalone HTTP client could not connect
to the Vercel domain, and the in-app browser blocked direct JSON `/health`
navigation. Anonymous HTTP and `/health` responses were therefore not
independently observed. Protection was verified in Vercel's saved configuration;
the real database was exercised by the signed-in app's saved chat APIs.
Google access still needs an explicit connection test with your own key.

For rollback, restore the preceding Vercel deployment while retaining All
Deployments protection and the dedicated database. Do not delete storage.
The previous local app remains runnable with its original Windows data and
settings; the cloud deployment never changes those files.

## M5 release · 5 October 2026

Commit `25f7c97` adds the Knowledge Library and L16–L18 without changing database
schema or infrastructure settings. A GitHub push completed; when an automatic
build had not appeared, Create Deployment resolved `main` to that exact commit
and Deploy to Production created `6GH8LmWvJ2Zr3faNVUfw9ggYga5n`. Vercel reported
Ready after 23 seconds. The production alias
[Knowledge Library](https://learn-llm-pi.vercel.app/library) loaded in the signed-in
browser. Offline mango evidence and missing-owner uncertainty returned correctly
with zero Google calls. No key, access-control setting, integration, progress,
or saved chat was changed during these checks. Live Google selection remains
unverified. See [M5 verification](M5_VALIDATION.md) for software proof and limits.
