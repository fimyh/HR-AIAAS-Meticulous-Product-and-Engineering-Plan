from fastapi import FastAPI

app = FastAPI(
    title="HR-AIAAS API",
    description="Local-first AI-assisted HR platform",
    version="0.1.0",
)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "HR-AIAAS API",
        "status": "running",
    }


@app.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
async def ready() -> dict[str, str]:
    return {"status": "ready"}
