from fastapi import FastAPI

from app.api import router as learner_router

app = FastAPI(
    title="TutorAI API",
    description="Local API for the TutorAI learning coach.",
    version="0.1.0",
)
app.include_router(learner_router)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "tutorai-api"}
