"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="Prije potpisa API",
    description="Okolišni pregled adrese u Hrvatskoj iz otvorenih podataka.",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)


@app.get("/api/health", tags=["sustav"])
def health() -> dict[str, str]:
    return {"status": "ok"}
