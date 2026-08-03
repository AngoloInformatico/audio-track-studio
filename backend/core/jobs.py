"""Small in-process job manager for cancellable local operations."""

import asyncio
from collections.abc import Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import RLock
from typing import Any
from uuid import uuid4

from backend.core.logging import get_logger
from backend.models.jobs import JobStatus, JobView

ProgressReporter = Callable[[float, str], None]
JobRunner = Callable[[ProgressReporter], Awaitable[dict[str, Any]]]


class JobNotFoundError(KeyError):
    """Raised when a job ID is unknown."""


@dataclass(slots=True)
class _JobRecord:
    id: str
    kind: str
    status: JobStatus = "pending"
    progress: float = 0.0
    message: str = "In attesa…"
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    task: asyncio.Task[None] | None = None


class JobManager:
    """Run jobs on the FastAPI event loop and expose immutable snapshots."""

    _instance: "JobManager | None" = None
    _instance_lock = RLock()

    def __init__(self) -> None:
        self._jobs: dict[str, _JobRecord] = {}
        self._lock = RLock()

    @classmethod
    def instance(cls) -> "JobManager":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def start(self, kind: str, runner: JobRunner) -> JobView:
        job_id = uuid4().hex
        record = _JobRecord(id=job_id, kind=kind)
        with self._lock:
            self._jobs[job_id] = record
            record.task = asyncio.create_task(self._execute(record, runner), name=f"ats-{kind}-{job_id}")
        return self._snapshot(record)

    def get(self, job_id: str) -> JobView:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                raise JobNotFoundError(job_id)
            return self._snapshot(record)

    async def cancel(self, job_id: str) -> JobView:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                raise JobNotFoundError(job_id)
            task = record.task
            if record.status in {"completed", "failed", "cancelled"} or task is None:
                return self._snapshot(record)
            record.message = "Annullamento in corso…"
            task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        return self.get(job_id)

    async def _execute(self, record: _JobRecord, runner: JobRunner) -> None:
        record.status = "running"
        record.message = "Avvio operazione…"

        def report(progress: float, message: str) -> None:
            with self._lock:
                if record.status == "running":
                    record.progress = max(0.0, min(99.9, float(progress)))
                    record.message = message

        try:
            result = await runner(report)
            with self._lock:
                record.status = "completed"
                record.progress = 100.0
                record.message = "Operazione completata"
                record.result = result
                record.finished_at = datetime.now(UTC)
        except asyncio.CancelledError:
            with self._lock:
                record.status = "cancelled"
                record.message = "Operazione annullata"
                record.finished_at = datetime.now(UTC)
            raise
        except Exception as exc:
            get_logger(__name__).exception("Job %s failed", record.id)
            with self._lock:
                record.status = "failed"
                record.message = "Operazione non riuscita"
                record.error = str(exc)
                record.finished_at = datetime.now(UTC)

    @staticmethod
    def _snapshot(record: _JobRecord) -> JobView:
        return JobView(
            id=record.id,
            kind=record.kind,
            status=record.status,
            progress=record.progress,
            message=record.message,
            result=record.result,
            error=record.error,
            created_at=record.created_at,
            finished_at=record.finished_at,
        )
