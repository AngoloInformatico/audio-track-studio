"""Rotating application logging without sensitive payloads."""

import logging
from logging.handlers import RotatingFileHandler

from backend.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    if any(getattr(handler, "name", None) == "ats-file" for handler in root.handlers):
        return
    handler = RotatingFileHandler(
        settings.log_dir / "audio-track-studio.log",
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.name = "ats-file"
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
