import logging
import uuid
from aiomysql import Connection, DictCursor
from app.api.dependencies import get_db
from app.core.security import (
    hash_password,
    create_access_token,
    create_refresh_token,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
)
from app.schemas.user import UserCreate, UserRegistrationResponse
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status


CHECK_QUERY = "SELECT UserUUID FROM User WHERE Username = %s"
INSERT_USER_QUERY = """
INSERT INTO User (UserUUID, Username, Password)
VALUES (%s, %s, %s)
"""
INSERT_RTOKEN_QUERY = """
INSERT INTO RefreshToken (UserUUID, Token, ExpiresAt, IsRevoked)
VALUES (%s, %s, %s, %s)
"""

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=UserRegistrationResponse
)
async def register_user(
    user_in: UserCreate, conn: Connection = Depends(get_db)
) -> UserRegistrationResponse:
    async with conn.cursor(DictCursor) as cursor:
        await cursor.execute(CHECK_QUERY, (user_in.username,))

        # Check if user already exists
        user_exists: bool = bool(await cursor.fetchone())
        if user_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="User already registered"
            )

        new_uuid: uuid.UUID = uuid.uuid4()
        uuid_bytes: bytes = new_uuid.bytes
        hashed_password: str = hash_password(user_in.password)
        access_token: str = create_access_token(str(new_uuid))
        refresh_token: str = create_refresh_token(str(new_uuid))
        expiry: datetime = datetime.now(timezone.utc) + timedelta(
            days=JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
        expires_at: str = expiry.strftime("%Y-%m-%d %H:%M:%S")

        try:
            await cursor.execute(
                INSERT_USER_QUERY, (uuid_bytes, user_in.username, hashed_password)
            )
            await cursor.execute(
                INSERT_RTOKEN_QUERY, (uuid_bytes, refresh_token, expires_at, False)
            )
            await conn.commit()
        except Exception as e:
            await conn.rollback()
            logger.error(
                f"Database Error occured during registration for {user_in.username}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A database error occured during registration.",
            )

        return UserRegistrationResponse(
            user_id=new_uuid,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
