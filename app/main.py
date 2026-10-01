"""Routes connect the browser to the content and progress services."""

from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
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


def create_app(database_path: Path | None = None, content_dir: Path | None = None, ai_settings=None, provider=None):
    content = ContentStore(content_dir or config.CONTENT_DIR)
    database = Database(database_path or config.DATABASE_PATH)
    progress = ProgressService(database, content)
    ai = AIService(ai_settings or config.AISettings.load(), database, content, provider)
    chats = ChatService(database, ai)
    app = FastAPI(title="Tiny Chat Lab", docs_url=None, redoc_url=None)
    app.state.content, app.state.progress, app.state.database = content, progress, database
    app.state.ai = ai
    app.state.chats = chats
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver", "[::1]"])
    app.mount("/static", StaticFiles(directory=config.APP_DIR / "static"), name="static")
    templates = Jinja2Templates(directory=config.APP_DIR / "templates")

    @app.middleware("http")
    async def local_guard(request: Request, call_next):
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            origin = request.headers.get("origin")
            current = urlsplit(str(request.base_url))
            supplied = urlsplit(origin) if origin else None
            if request.headers.get("sec-fetch-site") == "cross-site" or (supplied and (supplied.scheme, supplied.netloc) != (current.scheme, current.netloc)):
                return JSONResponse({"detail": "Use this app from its own local browser tab."}, status_code=403)
            if not request.headers.get("content-type", "").startswith("application/json"):
                return JSONResponse({"detail": "Send a JSON request."}, status_code=415)
            if len(await request.body()) > 32000:
                return JSONResponse({"detail": "That request is too large."}, status_code=413)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(ProgressError)
    async def progress_error(request, error):
        return JSONResponse({"detail": str(error)}, status_code=error.status)

    @app.exception_handler(AIError)
    async def ai_error(request, error):
        return JSONResponse({"detail": str(error), "code": error.code}, status_code=error.status)

    @app.exception_handler(KeyError)
    async def missing(request, error):
        return JSONResponse({"detail": "That lesson is not available yet."}, status_code=404)

    def render(request, template, **extra):
        summary = progress.summary()
        return templates.TemplateResponse(request=request, name=template, context={
            "course": content.course, "progress": summary, "page": template.removesuffix(".html"),
            "authored": content.lessons, "provider": ai.status(), **extra,
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
        return {"status": "ok", "milestone": "M3", "mode": ai.status()["mode"]}

    return app
