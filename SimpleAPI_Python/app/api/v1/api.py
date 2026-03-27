from app.api.v1.endpoints import auth, user, pin
from fastapi import APIRouter


api_router = APIRouter()

# Register a user
api_router.include_router(user.router, prefix="/users", tags=["Users"])
# Token obtaining/renewing
api_router.include_router(auth.router, prefix="/oauth", tags=["Authentication"])
# Pins CRUD
api_router.include_router(pin.router, prefix="/pins", tags=["Pins"])
