"""Isolated hosted-mode acceptance server; no real credentials or network."""
import os
from pathlib import Path

import httpx

from app.cloud_db import CloudDatabase
from app.cloud_settings import CloudSettingsStore
from app.config import ROOT
from app.main import create_app
from tests.browser_fixture import BrowserFake
from tests.test_cloud import SQLServer


def create_cloud_app():
    path = Path(os.environ['TINY_CHAT_DATABASE']).resolve()
    if not path.is_relative_to((ROOT/'data/browser-checks').resolve()):
        raise ValueError('Cloud browser fixture requires an isolated database.')
    server = SQLServer(path)
    database = CloudDatabase('libsql://test.turso.io','fake-database-token',httpx.MockTransport(server.request))
    return create_app(database=database,settings_store=CloudSettingsStore(database),hosted=True,provider=BrowserFake())
