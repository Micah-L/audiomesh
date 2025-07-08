from __future__ import annotations

from fastapi import FastAPI  # type: ignore[import-not-found]

app = FastAPI()


@app.get("/health")  # type: ignore[misc]
async def health() -> dict[str, str]:
    """Return service health status."""
    return {"status": "ok"}
