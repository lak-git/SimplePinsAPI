import bcrypt
import jwt
from app.core.config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
from datetime import datetime, timedelta, timezone
from typing import Any, Union


def hash_password(password: str) -> str:
    # Preparing Bytes
    salt: bytes = bcrypt.gensalt()
    password_bytes: bytes = password.encode("utf-8")

    hashed_password = bcrypt.hashpw(password=password_bytes, salt=salt)

    return hashed_password.decode("utf-8")


def verify_password(inpt_password: str, hashed_password: str) -> bool:
    password_bytes: bytes = inpt_password.encode("utf-8")
    hash_bytes: bytes = hashed_password.encode("utf-8")

    return bcrypt.checkpw(password=password_bytes, hashed_password=hash_bytes)


def create_access_token(user_uuid: Union[str, Any]) -> str:
    expiry: datetime = datetime.now(timezone.utc) + timedelta(
        minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    jwt_payload: dict = {
        "user_uuid": str(user_uuid),
        "type": "access",
        "expiry": int(expiry.timestamp()),
        "issued_at": int(datetime.now(timezone.utc).timestamp()),
    }

    return jwt.encode(jwt_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_uuid: Union[str, Any]) -> str:
    expiry: datetime = datetime.now(timezone.utc) + timedelta(
        days=JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    jwt_payload: dict = {
        "user_uuid": str(user_uuid),
        "type": "refresh",
        "expiry": int(expiry.timestamp()),
        "issued_at": int(datetime.now(timezone.utc).timestamp()),
    }

    return jwt.encode(jwt_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
