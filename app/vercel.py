"""Vercel's exported FastAPI entry point, with fail-closed cloud setup."""
import os
import threading

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.concurrency import run_in_threadpool

from app.cloud_db import CloudDatabase, CloudStorageError
from app.cloud_settings import CloudSettingsStore
from app.main import create_app


class HostedLab:
    def __init__(self):
        self.application = None
        self.lock = threading.Lock()

    def initialize(self):
        with self.lock:
            if self.application is None:
                if os.environ.get('TINY_CHAT_PRIVATE_HOSTING') != 'vercel-auth-all':
                    raise CloudStorageError('Enable Vercel Authentication for All Deployments, then set TINY_CHAT_PRIVATE_HOSTING to vercel-auth-all in the project settings.')
                database = CloudDatabase(os.environ.get('TURSO_DATABASE_URL', ''), os.environ.get('TURSO_AUTH_TOKEN', ''))
                hosts = ['127.0.0.1', 'localhost', 'testserver', '[::1]', '*.vercel.app']
                # Exact custom domains may be added; never allow every host.
                hosts.extend(value.strip() for value in os.environ.get('TINY_CHAT_HOSTS', '').split(',') if value.strip() and '*' not in value)
                self.application = create_app(database=database, settings_store=CloudSettingsStore(database), hosted=True, allowed_hosts=hosts)

    async def __call__(self, scope, receive, send):
        try:
            if self.application is None:
                await run_in_threadpool(self.initialize)
        except CloudStorageError:
            # No transient SQLite fallback and no credentials in error output.
            if scope['type'] != 'http':
                raise
            if scope['path'].startswith('/api/') or scope['path']=='/health':
                response = JSONResponse({'detail': 'Cloud storage is not ready. Connect Turso and enable private hosting in Vercel.', 'status': 'setup_required'}, status_code=503)
            else:
                response = HTMLResponse('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tiny Chat Lab · Cloud setup</title><body><main><h1>Tiny Chat Lab</h1><p>Your cloud lab is waiting for its database connection.</p><p>Connect a Turso database in this project’s Vercel Storage settings and enable Vercel Authentication for All Deployments. Set TINY_CHAT_PRIVATE_HOSTING to vercel-auth-all, then redeploy.</p><p>Google keys are added in the app’s Settings after setup. Your local learning data stays on your computer.</p></main></body></html>', status_code=503)
            response.headers['Cache-Control'] = 'no-store'
            await response(scope, receive, send)
            return
        await self.application(scope, receive, send)


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount('/', HostedLab())
