import uuid
from ..core.security import hash_password, create_access_token, create_refresh_token
from ..core.config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_REFRESH_TOKEN_EXPIRE_DAYS
from ..models import user as model
from aiomysql import DictCursor
from datetime import datetime, timedelta, timezone
from typing import Tuple


async def check_user_exists(cursor: DictCursor, username: str) -> bool:
    return bool(await model.get_user(cursor, username))


async def register_user(
    cursor: DictCursor, username: str, password: str
) -> Tuple[uuid.UUID, str, str, int]:
    new_uuid: uuid.UUID = uuid.uuid4()
    uuid_bytes: bytes = new_uuid.bytes
    hashed_password: str = hash_password(password)
    access_token: str = create_access_token(str(new_uuid))
    refresh_token: str = create_refresh_token(str(new_uuid))
    expiry: datetime = datetime.now(timezone.utc) + timedelta(
        days=JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    expires_at: str = expiry.strftime("%Y-%m-%d %H:%M:%S")

    await model.add_user(cursor, uuid_bytes, username, hashed_password)
    await model.add_refresh_token(cursor, uuid_bytes, refresh_token, expires_at, False)

    return (new_uuid, access_token, refresh_token, JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60)

