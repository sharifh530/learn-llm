"""Routes connect the browser to the content and progress services."""

from pathlib import Path
from contextvars import ContextVar
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app import config
from app.content import ContentError, ContentStore
from app.db import Database
from app.demo import reply
from app.models import Acknowledgment, Attempt, DemoMessage, Journal, AIMessage, TutorMessage, ConnectionTest
from app.ai import AIService
from app.providers import AIError
from app.progress import ProgressError, ProgressService
from app.chat import ChatService, PERSONAS
from app.models import ChatCreate, ChatUpdate, ChatRetry, ChatSelection, ChatContext, EmptyInput
from app.models import SimilarityToy, AttentionToy, TrainingToy
from app.models import ProviderSettings
from app.settings_store import SettingsStore, SettingsStoreError
from app import labs
from app.library import LibraryService, chunks
from app.models import LibrarySearch, LibraryQuestion, ChunkPreview


def create_app(database_path: Path | None = None, content_dir: Path | None = None, ai_settings=None, provider=None, *, database=None, settings_store=None, hosted=False, allowed_hosts=None):
    content = ContentStore(content_dir or config.CONTENT_DIR)
    database = database or Database(database_path or config.DATABASE_PATH)
    progress = ProgressService(database, content)
    library = LibraryService(content)
    settings_store = settings_store or SettingsStore(database.path.parent / 'ai-settings.json')
    settings_notice = ''
    if ai_settings is None:
        try:
            ai_settings = settings_store.load()
        except SettingsStoreError as error:
            ai_settings, settings_notice = config.AISettings(), str(error)
    ai = AIService(ai_settings, database, content, provider)
    ai.settings_store = settings_store
    ai.settings_notice = settings_notice
    chats = ChatService(database, ai)
    # Cloud instances never share mutable credentials or worker dictionaries
    # between requests. SQLite remains the unchanged local default.
    request_services = ContextVar('tiny_chat_services')
    if hosted:
        class ServiceProxy:
            def __init__(self, name):
                self.name = name
            def __getattr__(self, name):
                return getattr(request_services.get()[self.name], name)
        ai, chats = ServiceProxy('ai'), ServiceProxy('chats')
    app = FastAPI(title="Tiny Chat Lab", docs_url=None, redoc_url=None)
    app.state.content, app.state.progress, app.state.database = content, progress, database
    app.state.ai = ai
    app.state.chats = chats
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts or ["127.0.0.1", "localhost", "testserver", "[::1]"])
    app.mount("/static", StaticFiles(directory=config.APP_DIR / "static"), name="static")
    templates = Jinja2Templates(directory=config.APP_DIR / "templates")

    @app.middleware("http")
    async def local_guard(request: Request, call_next):
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            origin = request.headers.get("origin")
            current = urlsplit(str(request.base_url))
            supplied = urlsplit(origin) if origin else None
            if request.headers.get("sec-fetch-site") == "cross-site" or (supplied and (supplied.scheme, supplied.netloc) != (current.scheme, current.netloc)):
                return JSONResponse({"detail": "Use this app from its own browser tab."}, status_code=403)
            if not request.headers.get("content-type", "").startswith("application/json"):
                return JSONResponse({"detail": "Send a JSON request."}, status_code=415)
            if len(await request.body()) > 32000:
                return JSONResponse({"detail": "That request is too large."}, status_code=413)
        token = None
        if hosted:
            from starlette.concurrency import run_in_threadpool
            def services():
                notice = ''
                try:
                    settings = settings_store.load()
                except SettingsStoreError as error:
                    settings, notice = config.AISettings(), str(error)
                service = AIService(settings, database, content, provider)
                service.settings_store = settings_store
                service.settings_notice = notice
                return {'ai': service, 'chats': ChatService(database, service)}
            try:
                token = request_services.set(await run_in_threadpool(services))
            except Exception as error:
                from app.cloud_db import CloudStorageError
                if not isinstance(error, CloudStorageError):
                    raise
                return JSONResponse({'detail': str(error)}, status_code=503, headers={'Cache-Control':'no-store'})
        try:
            response = await call_next(request)
        finally:
            if token is not None:
                request_services.reset(token)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(ProgressError)
    async def progress_error(request, error):
        return JSONResponse({"detail": str(error)}, status_code=error.status)

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request, error):
        # Raw invalid values can include NaN/Infinity or exception objects.
        # Return stable field diagnostics without echoing unserializable inputs.
        details = [{key: item[key] for key in ("type", "loc", "msg")} for item in error.errors()]
        return JSONResponse({"detail": details}, status_code=422)

    @app.exception_handler(AIError)
    async def ai_error(request, error):
        return JSONResponse({"detail": str(error), "code": error.code}, status_code=error.status)

    @app.exception_handler(SettingsStoreError)
    async def settings_error(request, error):
        return JSONResponse({"detail": str(error)}, status_code=400)

    @app.exception_handler(KeyError)
    async def missing(request, error):
        return JSONResponse({"detail": "That lesson is not available yet."}, status_code=404)

    if hosted:
        from app.cloud_db import CloudStorageError
        @app.exception_handler(CloudStorageError)
        async def cloud_storage_error(request, error):
            return JSONResponse({'detail': str(error)}, status_code=503)

    def render(request, template, **extra):
        summary = progress.summary()
        return templates.TemplateResponse(request=request, name=template, context={
            "course": content.course, "progress": summary, "page": template.removesuffix(".html"),
            "authored": content.lessons, "provider": ai.status(), "hosted": hosted, **extra,
        })

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        return render(request, "home.html")

    @app.get("/lessons/{lesson_id}", response_class=HTMLResponse)
    def lesson(request: Request, lesson_id: str):
        if lesson_id not in content.lessons:
            entry = next((entry for entry in content.course["lessons"] if entry["id"] == lesson_id), None)
            return render(request, "unavailable.html", entry=entry)
        current = content.lesson(lesson_id)
        progress.visit(current)
        available = list(content.lessons)
        position = available.index(lesson_id)
        next_id = available[position + 1] if position + 1 < len(available) else None
        return render(request, "lesson.html", lesson=current, next_id=next_id, entries=progress.journals(lesson_id))

    @app.get("/workshop", response_class=HTMLResponse)
    def workshop(request: Request):
        return render(request, "workshop.html", entries=progress.journals())

    @app.get('/observatory',response_class=HTMLResponse)
    def observatory(request: Request):
        return render(request,'observatory.html',fruits=labs.FRUITS,words=labs.WORDS)

    @app.get('/library', response_class=HTMLResponse)
    def knowledge_library(request: Request):
        return render(request, 'library.html', catalog=library.catalog())

    @app.get('/api/library')
    def library_catalog():
        return library.catalog()

    @app.post('/api/library/chunks')
    def preview_chunks(body: ChunkPreview):
        return {'chunks': chunks(body.text, body.words), 'words': body.words, 'saved': False}

    @app.post('/api/library/search')
    def retrieve_notes(body: LibrarySearch):
        return library.retrieve(body)

    @app.post('/api/library/answers')
    def answer_from_notes(body: LibraryQuestion):
        return library.answer(body, ai)

    @app.post('/api/labs/similarity')
    def similarity_toy(body: SimilarityToy):
        return labs.similarity(body.vector)

    @app.post('/api/labs/attention')
    def attention_toy(body: AttentionToy):
        return labs.attention(body.scores,body.query_index,body.causal,body.temperature)

    @app.post('/api/labs/training')
    def training_toy(body: TrainingToy):
        return labs.training(body.weight,body.learning_rate,body.steps,body.operation)

    @app.get("/chat", response_class=HTMLResponse)
    def chat(request: Request):
        return render(request, "chat.html", personas=PERSONAS)

    @app.get("/settings", response_class=HTMLResponse)
    def settings(request: Request):
        return render(request, "settings.html")

    @app.get("/api/course")
    def course():
        return content.course

    @app.get("/api/lessons/{lesson_id}")
    def lesson_data(lesson_id: str):
        return content.lesson(lesson_id)

    @app.get("/api/progress")
    def current_progress():
        return progress.summary()

    @app.post("/api/attempts")
    def attempt(body: Attempt):
        result = progress.attempt(body)
        return {**result, "progress": progress.summary()}

    @app.post("/api/lessons/{lesson_id}/acknowledgments")
    def acknowledge(lesson_id: str, body: Acknowledgment):
        return progress.acknowledge(content.lesson(lesson_id), body.kind, body.version)

    @app.get("/api/journal")
    def journal_entries():
        return progress.journals()

    @app.post("/api/journal")
    def journal(body: Journal):
        return progress.save_journal(body)

    @app.get("/api/provider/status")
    def provider_status():
        return ai.status()

    @app.post("/api/provider/test")
    def connection_test(body: ConnectionTest):
        return ai.request("connection", body)

    @app.post('/api/provider/settings')
    def save_provider_settings(body: ProviderSettings):
        with chats.lock:
            if chats.jobs:
                raise AIError('busy', 'Wait for the current reply to finish before changing the connection.', 409)
            return ai.configure(settings_store, body)

    @app.post('/api/provider/key/remove')
    def remove_provider_key(body: EmptyInput):
        with chats.lock:
            if chats.jobs:
                raise AIError('busy', 'Wait for the current reply to finish before changing the connection.', 409)
            return ai.configure(settings_store)

    @app.post("/api/ai/messages")
    def ai_message(body: AIMessage):
        return ai.request("chat", body)

    @app.post("/api/tutor/messages")
    def tutor_message(body: TutorMessage):
        return ai.request("tutor", body)

    @app.post("/api/demo/messages")
    def demo_message(body: DemoMessage):
        return {"reply": reply(body.message), "mode": "demo", "network_calls": 0}

    @app.get('/api/chats')
    def saved_chats(mode: str = 'demo', archived: bool = False):
        if mode not in ('demo','google_cloud'):
            raise HTTPException(422,'Choose Demo or Google mode.')
        return chats.list(mode,archived)

    @app.post('/api/chats')
    def create_chat(body: ChatCreate):
        return chats.create(body)

    @app.get('/api/chats/{chat_id}')
    def saved_chat(chat_id: str):
        return chats.get(chat_id)

    @app.post('/api/chats/{chat_id}/settings')
    def update_chat(chat_id: str, body: ChatUpdate):
        return chats.update(chat_id,body)

    @app.post('/api/chats/{chat_id}/archive')
    def archive_chat(chat_id: str, body: EmptyInput):
        return chats.archive(chat_id,True)

    @app.post('/api/chats/{chat_id}/restore')
    def restore_chat(chat_id: str, body: EmptyInput):
        return chats.archive(chat_id,False)

    @app.post('/api/chats/{chat_id}/context')
    def chat_context(chat_id: str, body: ChatContext):
        return chats.context(chat_id,body.message)

    @app.post('/api/chats/{chat_id}/messages')
    def chat_message(chat_id: str, body: AIMessage):
        return chats.start(chat_id,body)

    @app.post('/api/chats/{chat_id}/turns/{turn_id}/retry')
    def chat_retry(chat_id: str, turn_id: str, body: ChatRetry):
        return chats.start(chat_id,body,turn_id)

    @app.post('/api/chats/{chat_id}/turns/{turn_id}/select')
    def chat_select(chat_id: str, turn_id: str, body: ChatSelection):
        return chats.select(chat_id,turn_id,body)

    @app.get('/api/generations/{identity}')
    def generation(identity: str):
        return chats.generation(identity)

    @app.get('/api/generations/{identity}/events')
    def chat_events(identity: str):
        chats.generation(identity)
        return StreamingResponse(chats.events(identity),media_type='text/event-stream',headers={'X-Accel-Buffering':'no'})

    @app.post('/api/generations/{identity}/cancel')
    def chat_cancel(identity: str, body: EmptyInput):
        return chats.cancel(identity)

    @app.post("/api/content/reload")
    def reload_content():
        try:
            return content.reload()
        except ContentError as error:
            raise HTTPException(status_code=400, detail=f"Content was not published. {error}") from error

    @app.get("/health")
    def health():
        return {"status": "ok", "milestone": "M5", "mode": ai.status()["mode"], "storage": "cloud" if hosted else "local"}

    return app
