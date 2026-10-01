"""Explicit test-only server factory; requires a database under data/browser-checks."""
import os
import time
from pathlib import Path

from app.config import AISettings, ROOT
from app.main import create_app as application
from app.providers import AIError, ModelReply
from tests.test_ai import FakeProvider


class BrowserFake(FakeProvider):
    def stream(self,instruction,messages,input_limit,output_limit,on_call,cancelled):
        self.calls.append((instruction,messages,input_limit,output_limit))
        on_call();on_call()
        question=messages[-1]['text']
        yield ModelReply('TEST FAKE: first chunk. ')
        for _ in range(80 if 'slow' in question else 4):
            if cancelled():
                return
            time.sleep(.04)
        if 'simulate error' in question:
            raise AIError('test_error','TEST FAKE: simulated failure. Your question is preserved.')
        yield ModelReply('Earlier user: '+messages[0]['text'])
        yield ModelReply('',20,10,30,'STOP')

    def generate(self, *arguments):
        if 'simulate error' in arguments[1]:
            self.calls.append(arguments[:4])
            arguments[-1]()
            raise AIError('test_error', 'TEST FAKE: simulated failure. Your question is preserved.')
        return super().generate(*arguments)


def create_app():
    path = Path(os.environ['TINY_CHAT_DATABASE']).resolve()
    if not path.is_relative_to((ROOT / 'data/browser-checks').resolve()):
        raise ValueError('Test factory requires an isolated browser-checks database.')
    return application(path, ai_settings=AISettings(enabled=True, api_key='test-only-fake-key', model='test-only-model'), provider=BrowserFake())
