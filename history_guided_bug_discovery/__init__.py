"""Repository-local import shim; implementation lives under ``src/``."""

from pathlib import Path

__path__ = [str(Path(__file__).resolve().parent.parent / "src" / "history_guided_bug_discovery")]
__version__ = "1.0.0"
