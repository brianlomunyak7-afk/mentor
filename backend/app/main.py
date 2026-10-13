from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as learner_router
from app.config import get_settings
from app.rate_limit import InMemoryRateLimiter, rate_limit_middleware

app = FastAPI(
    title="TutorAI API",
    description="Local API for the TutorAI learning coach.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(
    rate_limit_middleware(
        InMemoryRateLimiter(get_settings().api_rate_limit_per_minute)
    )
)
app.include_router(learner_router)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "tutorai-api"}
