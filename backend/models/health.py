"""Health endpoint models."""

from typing import Literal

from pydantic import BaseModel


class ToolStatus(BaseModel):
    available: bool
    version: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    version: str
    tools: dict[str, ToolStatus]
