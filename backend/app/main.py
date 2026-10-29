from fastapi import FastAPI

app = FastAPI(
    title="TutorAI API",
    description="Local API for the TutorAI learning coach.",
    version="0.1.0",
)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "tutorai-api"}
