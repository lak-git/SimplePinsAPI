import asyncio
import aiomysql
from app.core.config import HOST, USER, PASSWORD, DATABASE
from contextlib import asynccontextmanager
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


MAX_CONCURRENT_QUERIES = 10


class DatabaseManager:
    def __init__(self, host, user, password, database) -> None:
        self.config = {
            "host": host,
            "user": user,
            "password": password,
            "db": database,
            "autocommit": False,
        }
        self.pool = None
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_QUERIES)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(aiomysql.OperationalError),
        reraise=True,
    )
    async def initialize(self) -> None:
        """Creates connection pool on app startup"""
        self.pool = await aiomysql.create_pool(
            **self.config, minsize=1, maxsize=MAX_CONCURRENT_QUERIES
        )

    @asynccontextmanager
    async def get_connection(self):
        """Acquires a connection from the pool, governed by the semaphore."""
        if not self.pool:
            raise RuntimeError("Database Pool not initialized. Run initialize()")

        async with self.semaphore:
            async with self.pool.acquire() as connection:
                yield connection

    async def close(self) -> None:
        """Gracefully closes all connections."""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()


db_manager = DatabaseManager(host=HOST, user=USER, password=PASSWORD, database=DATABASE)
