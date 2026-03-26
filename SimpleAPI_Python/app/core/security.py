import bcrypt
import jwt
from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM
from datetime import datetime, timedelta, timezone
from typing import Any, Union


JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 15
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    # Preparing Bytes
    salt: bytes = bcrypt.gensalt()
    password_bytes: bytes = password.encode("utf-8")

    hashed_password = bcrypt.hashpw(password=password_bytes, salt=salt)

    return hashed_password.decode("utf-8")


def create_access_token(user_uuid: Union[str, Any]) -> str:
    expiry: datetime = datetime.now(timezone.utc) + timedelta(
        minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    jwt_payload: dict = {
        "user_uuid": str(user_uuid),
        "type": "access",
        "expiry": expiry,
        "issued_at": datetime.now(timezone.utc),
    }

    return jwt.encode(jwt_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_uuid: Union[str, Any]) -> str:
    expiry: datetime = datetime.now(timezone.utc) + timedelta(
        days=JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    jwt_payload: dict = {
        "user_uuid": str(user_uuid),
        "type": "refresh",
        "expiry": expiry,
        "issued_at": datetime.now(timezone.utc),
    }

    return jwt.encode(jwt_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
