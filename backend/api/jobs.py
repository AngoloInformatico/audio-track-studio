"""Long-running job status and cancellation endpoints."""

from fastapi import APIRouter, HTTPException, status

from backend.core.jobs import JobManager, JobNotFoundError
from backend.models.jobs import JobView

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobView)
async def get_job(job_id: str) -> JobView:
    try:
        return JobManager.instance().get(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job non trovato.") from exc


@router.delete("/{job_id}", response_model=JobView)
async def cancel_job(job_id: str) -> JobView:
    try:
        return await JobManager.instance().cancel(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job non trovato.") from exc
