"""Development launcher: python -m backend."""

import uvicorn

from backend.core.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("backend.main:app", host=settings.host, port=settings.port, reload=True)
