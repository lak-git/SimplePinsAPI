from app.db.database import db_manager
from app.api.v1.api import api_router
from app.core.limiter import limiter
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded


@asynccontextmanager
async def lifespan(app: FastAPI):
    # StartUp
    await db_manager.initialize()
    yield
    # Shutdown (Ctrl + C)
    await db_manager.close()


app = FastAPI(
    title="Simple Pins API",
    description="Simple Pins API implementation with OAuth + Unit Testing, for Week 2 Dev Onboarding",
    version="1.1.0",
    lifespan=lifespan,
)
# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# CORS
origins = ["http://localhost", "http://127.0.0.1", "http://127.0.0.1:8000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Routing
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"status": "online", "message": "API Active"}
