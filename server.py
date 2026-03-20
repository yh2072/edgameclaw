"""Backward-compatible ASGI entrypoint when running from the repo root.

Prefer: ``uvicorn edgameclaw.server:app`` or ``pip install -e .`` then the same.
"""

from edgameclaw.server import app

__all__ = ["app"]
