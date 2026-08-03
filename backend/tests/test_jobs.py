import asyncio

from backend.core.jobs import JobManager


def test_job_manager_completes_and_reports_progress() -> None:
    async def scenario() -> None:
        manager = JobManager()

        async def runner(report):
            report(42, "Metà lavoro")
            await asyncio.sleep(0)
            return {"files": ["track.flac"]}

        started = manager.start("export", runner)
        assert started.status == "pending"
        await asyncio.sleep(0.01)
        completed = manager.get(started.id)
        assert completed.status == "completed"
        assert completed.progress == 100
        assert completed.result == {"files": ["track.flac"]}

    asyncio.run(scenario())


def test_job_manager_cancels_runner() -> None:
    async def scenario() -> None:
        manager = JobManager()

        async def runner(report):
            report(10, "Avvio")
            await asyncio.Event().wait()
            return {}

        started = manager.start("export", runner)
        await asyncio.sleep(0)
        cancelled = await manager.cancel(started.id)
        assert cancelled.status == "cancelled"
        assert cancelled.finished_at is not None

    asyncio.run(scenario())
