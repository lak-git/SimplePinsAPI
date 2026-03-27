import jwt
import uuid
from aiomysql import Connection, DictCursor
from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM
from app.db.database import db_manager
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import AsyncGenerator, Dict


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/oauth/token")


async def get_db() -> AsyncGenerator[Connection, None]:
    """
    Dependency injection function to yield database connection
    """
    async with db_manager.get_connection() as conn:
        yield conn


CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)
SELECT_QUERY = "SELECT Username FROM User WHERE UserUUID = %s"


async def get_current_user(
    token: str = Depends(oauth2_scheme), conn: Connection = Depends(get_db)
) -> dict:
    """
    Validates the JWT access token and returns the current user's UUID (in bytes) and Username.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        invalid_token_type: bool = payload.get("type") != "access"
        if invalid_token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type."
            )
        user_uuid: str = payload.get("user_uuid")
        invalid_user: bool = user_uuid is None
        if invalid_user:
            raise CREDENTIALS_EXCEPTION
    except jwt.PyJWTError:
        raise CREDENTIALS_EXCEPTION

    try:
        user_uuid_obj = uuid.UUID(user_uuid)
        user_uuid_bytes: bytes = user_uuid_obj.bytes
    except ValueError:
        raise CREDENTIALS_EXCEPTION

    async with conn.cursor(DictCursor) as cursor:
        await cursor.execute(SELECT_QUERY, (user_uuid_bytes))
        user = await cursor.fetchone()

        no_user_found: bool = user is None
        if no_user_found:
            raise CREDENTIALS_EXCEPTION

    return {"user_uuid": user_uuid_bytes, "username": user["Username"]}
