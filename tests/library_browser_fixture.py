"""Disposable UI fixture. Its provider never contacts Google."""
import json
from app.config import AISettings
from app.main import create_app
from tests.test_library import EvidenceProvider


class BrowserEvidenceProvider(EvidenceProvider):
    def generate(self,instruction,message,*args):
        if json.loads(message)['question']=='mango forged':
            self.corrupt=lambda result:{**result,'evidence':[{'source_id':'invented','quote':'forged secret claim'}]}
        try:
            return super().generate(instruction,message,*args)
        finally:
            self.corrupt=None


def create_library_app():
    return create_app(ai_settings=AISettings(enabled=True,api_key='FAKE-NOT-A-REAL-GOOGLE-KEY',model='FAKE-M5'),provider=BrowserEvidenceProvider())
