import jwt
import uuid
from ..core.config import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
)
from ..core.security import create_access_token, create_refresh_token, verify_password
from ..models import auth as model
from aiomysql import DictCursor
from datetime import datetime, timedelta, timezone
from typing import Any, Tuple


async def check_invalid_username_password(
    cursor: DictCursor, username: str, password: str
) -> bool:
    user_record = await model.get_user_record(cursor, username)
    state: bool = not user_record or not verify_password(
        password, user_record["Password"]
    )
    return state


async def save_refresh_token(cursor: DictCursor, username: str) -> Tuple[str, str, int]:
    user_record = await model.get_user_record(cursor, username)
    user_uuid: str = str(uuid.UUID(bytes=user_record["UserUUID"]))
    access_token: str = create_access_token(user_uuid)
    refresh_token: str = create_refresh_token(user_uuid)
    expiry: datetime = datetime.now(timezone.utc) + timedelta(
        days=JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    expires_at: str = expiry.strftime("%Y-%m-%d %H:%M:%S")

    await model.add_refresh_token(
        cursor, user_record["UserUUID"], refresh_token, expires_at, False
    )

    return (access_token, refresh_token, JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60)


async def check_rtoken_exists(cursor: DictCursor, refresh_token: str) -> bool:
    db_token = await model.get_refresh_token(cursor, refresh_token)
    return not db_token


async def check_rtoken_is_revoked(cursor: DictCursor, refresh_token: str) -> bool:
    db_token = await model.get_refresh_token(cursor, refresh_token)
    return db_token["IsRevoked"]


def check_valid_token_type(token: str, type: str) -> Tuple[bool, str]:
    payload: dict[str, Any] = jwt.decode(
        token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
    )
    state: bool = payload.get("type") != type
    user_uuid: str = str(payload.get("user_uuid"))
    return (state, user_uuid)


def renew_tokens(user_uuid: str) -> Tuple[str, str, int]:
    new_access_token: str = create_access_token(user_uuid)
    new_refresh_token: str = create_refresh_token(user_uuid)
    expires_in = JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

    return (new_access_token, new_refresh_token, expires_in)
