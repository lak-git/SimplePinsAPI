from aiomysql import DictCursor


SELECT_USER_QUERY = "SELECT UserUUID, Password FROM User WHERE Username = %s"
SELECT_RTOKEN_QUERY = """
SELECT IsRevoked FROM RefreshToken 
WHERE Token = %s
"""
INSERT_RTOKEN_QUERY = """
INSERT INTO RefreshToken (UserUUID, Token, ExpiresAt, IsRevoked)
VALUES (%s, %s, %s, %s)
"""


async def get_user_record(cursor: DictCursor, username: str):
    await cursor.execute(SELECT_USER_QUERY, (username,))
    return await cursor.fetchone()


async def get_refresh_token(cursor: DictCursor, refresh_token: str):
    await cursor.execute(SELECT_RTOKEN_QUERY, (refresh_token,))
    return await cursor.fetchone()


async def add_refresh_token(
    cursor: DictCursor,
    user_uuid: bytes,
    refresh_token: str,
    expires_at: str,
    is_revoked: bool,
):
    await cursor.execute(
        INSERT_RTOKEN_QUERY, (user_uuid, refresh_token, expires_at, is_revoked)
    )

