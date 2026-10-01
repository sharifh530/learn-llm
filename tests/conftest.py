"""Keep disposable test files in this project, away from shared Windows temp."""
from pathlib import Path
from uuid import uuid4


def pytest_configure(config):
    if config.option.basetemp is None:
        root = Path(__file__).resolve().parents[1]
        destination = (root / "data" / "test-runs" / uuid4().hex).resolve()
        assert destination.is_relative_to(root.resolve()) and not destination.exists()
        destination.parent.mkdir(parents=True, exist_ok=True)
        config.option.basetemp = str(destination)
