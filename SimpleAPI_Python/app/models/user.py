from aiomysql import DictCursor


SELECT_USER_QUERY = "SELECT UserUUID FROM User WHERE Username = %s"
INSERT_USER_QUERY = """
INSERT INTO User (UserUUID, Username, Password)
VALUES (%s, %s, %s)
"""
INSERT_RTOKEN_QUERY = """
INSERT INTO RefreshToken (UserUUID, Token, ExpiresAt, IsRevoked)
VALUES (%s, %s, %s, %s)
"""


async def get_user(cursor: DictCursor, username: str):
    await cursor.execute(SELECT_USER_QUERY, (username,))
    return await cursor.fetchone()


async def add_user(cursor: DictCursor, uuid: bytes, username: str, password: str):
    await cursor.execute(INSERT_USER_QUERY, (uuid, username, password))


async def add_refresh_token(
    cursor: DictCursor,
    uuid: bytes,
    refresh_token: str,
    expires_at: str,
    is_revoked: bool,
):
    await cursor.execute(
        INSERT_RTOKEN_QUERY, (uuid, refresh_token, expires_at, is_revoked)
    )
