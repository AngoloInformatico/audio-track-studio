"""Models shared by long-running backend jobs."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

JobStatus = Literal["pending", "running", "completed", "failed", "cancelled"]


class JobView(BaseModel):
    id: str
    kind: str
    status: JobStatus
    progress: float = Field(ge=0, le=100)
    message: str
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime
    finished_at: datetime | None = None
