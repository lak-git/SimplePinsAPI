from app.api.v1.endpoints import user
from fastapi import APIRouter


api_router = APIRouter()

api_router.include_router(user.router, prefix="/users", tags=["Users"])

