import pytest
from app.main import app
from app.api.dependencies import get_db
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_cursor():
    """
    Fake Asynchronous DB Cursor.
    """
    cursor = AsyncMock()
    return cursor


@pytest.fixture
def mock_conn(mock_cursor):
    # For connection
    conn = MagicMock()
    # For context manager
    mock_ctx = AsyncMock()

    mock_ctx.__aenter__.return_value = mock_cursor
    mock_ctx.__aexit__.return_value = None
    # Special context manager
    conn.cursor.return_value = mock_ctx

    # Commit needs AsyncMock
    conn.commit = AsyncMock()
    conn.rollback = AsyncMock()

    return conn


@pytest.fixture
def client(mock_conn):
    """
    Creates a client with the database depnedency overriden to use mock data
    """

    # Override database
    async def override_get_db():
        yield mock_conn

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
