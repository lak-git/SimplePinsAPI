from app.db.database import db_manager
from contextlib import asynccontextmanager
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    # StartUp
    await db_manager.initialize()
    yield
    # Shutdown (Ctrl + C)
    await db_manager.close()


app = FastAPI(
    title="Simple Pins API",
    description="Simple Pins API implementation with OAuth, for Week 2 Dev Onboarding",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {"status": "online", "message": "API Active"}
