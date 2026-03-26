from app.api.v1.endpoints import auth, user
from fastapi import APIRouter


api_router = APIRouter()

# Register a user
api_router.include_router(user.router, prefix="/users", tags=["Users"])
# Obtain a new token/login
api_router.include_router(auth.router, prefix="/oauth", tags=["Authentication"])
