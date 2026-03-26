from aiomysql import Connection
from app.db.database import db_manager
from typing import AsyncGenerator


async def get_db() -> AsyncGenerator[Connection, None]:
    """ "
    Dependency injection function to yield database connection
    """
    async with db_manager.get_connection() as conn:
        yield conn
