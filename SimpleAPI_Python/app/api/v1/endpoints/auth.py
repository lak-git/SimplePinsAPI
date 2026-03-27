import jwt
import logging
import uuid
from app.api.dependencies import get_db
from app.core.config import JWT_ALGORITHM, JWT_SECRET_KEY
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
)
from app.schemas.token import TokenResponse, RefreshToken
from aiomysql import Connection, DictCursor
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm


SELECT_QUERY = "SELECT UserUUID, Password FROM User WHERE Username = %s"
CHECK_RTOKEN_QUERY = """
SELECT IsRevoked FROM RefreshToken 
WHERE Token = %s
"""
INSERT_RTOKEN_QUERY = """
INSERT INTO RefreshToken (UserUUID, Token, ExpiresAt, IsRevoked)
VALUES (%s, %s, %s, %s)
"""

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/token", response_model=TokenResponse)
async def obtain_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), conn: Connection = Depends(get_db)
) -> TokenResponse:
    async with conn.cursor(DictCursor) as cursor:
        await cursor.execute(SELECT_QUERY, (form_data.username))
        user_record = await cursor.fetchone()

        invalid_username_password: bool = not user_record or not verify_password(
            form_data.password, user_record["Password"]
        )
        if invalid_username_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_uuid: str = str(uuid.UUID(bytes=user_record["UserUUID"]))
        access_token: str = create_access_token(user_uuid)
        refresh_token: str = create_refresh_token(user_uuid)
        expiry: datetime = datetime.now(timezone.utc) + timedelta(
            days=JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
        expires_at: str = expiry.strftime("%Y-%m-%d %H:%M:%S")

        try:
            await cursor.execute(
                INSERT_RTOKEN_QUERY,
                (user_record["UserUUID"], refresh_token, expires_at, False),
            )
            await conn.commit()
        except Exception as e:
            await conn.rollback()
            logger.error(
                f"Failed to store refresh token for user {form_data.username} at /tokens: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A database error occured when obtaining token.",
            )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )


@router.post("/refresh", response_model=TokenResponse)
async def renew_acess_token(
    request: RefreshToken, conn: Connection = Depends(get_db)
) -> TokenResponse:
    try:
        payload = jwt.decode(
            request.refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
        )
        invalid_type: bool = payload.get("type") != "refresh"
        if invalid_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        user_uuid: str = str(payload.get("user_uuid"))

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token has expired.",
        )
    except jwt.PyJWTError as e:
        logger.error(f"JWT Decoding Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials!!",
        )

    async with conn.cursor(DictCursor) as cursor:
        await cursor.execute(CHECK_RTOKEN_QUERY, (request.refresh_token,))
        db_token = await cursor.fetchone()

        token_not_found: bool = not db_token
        revoked_token: bool = db_token["IsRevoked"]
        if token_not_found:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh Token not found in database.",
            )
        if revoked_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh Token is revoked.",
            )

    # TODO: Insert new Refresh Token and revoke old one.
    new_access_token: str = create_access_token(user_uuid)
    new_refresh_token: str = create_refresh_token(user_uuid)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
