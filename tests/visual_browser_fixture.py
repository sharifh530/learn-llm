"""Disposable lesson content and learner storage, with AI disabled."""
import os
from pathlib import Path
from app.main import create_app as application
from app.config import ROOT, AISettings


def create_app():
    path=Path(os.environ['TINY_CHAT_DATABASE']).resolve()
    if not path.is_relative_to((ROOT/'data/browser-checks').resolve()):
        raise ValueError('Visual UI checks require disposable browser-checks storage.')
    return application(path,path.parent/'content',ai_settings=AISettings())
