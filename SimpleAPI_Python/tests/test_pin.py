import pytest
from app.api.dependencies import get_current_user
from app.main import app
from datetime import datetime, timezone


MOCK_USER = {"user_uuid": b"PT_UUID", "username": "PT_Username"}


def override_get_current_user():
    return MOCK_USER


@pytest.fixture(autouse=True)
def mock_auth():
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


def test_PT01(client, mock_cursor, mock_conn):
    """
    Test Case: Create a pin successfully with valid data
    Expected: 201 Created and the returned PinResponse data
    """
    mock_cursor.lastrowid = 101
    fake_time = datetime.now(timezone.utc)
    mock_cursor.fetchone.return_value = {"CreatedAt": fake_time}
    test_payload = {
        "title": "PT01 Title",
        "body": "This is a test description.",
        "image_link": "https://example.com/image.png",
    }

    response = client.post("/api/v1/pins/", json=test_payload)

    assert response.status_code == 201
    data = response.json()
    assert data["pin_id"] == 101
    assert data["author"] == "PT_Username"  # From MOCK_USER
    assert data["title"] == test_payload["title"]

    mock_conn.commit.assert_awaited_once()


def test_PT02(client, mock_cursor, mock_conn):
    """
    Test Case: Simulate a database crash during insertion
    Expected: 500 Internal Server Error and transaction rollback
    """
    mock_cursor.execute.side_effect = Exception("Simulated Database Crash")
    test_payload = {"title": "PT02 Title", "body": "This will crash the DB"}

    response = client.post("/api/v1/pins/", json=test_payload)

    assert response.status_code == 500
    assert response.json() == {"detail": "A database error occured while creating pin."}

    mock_conn.rollback.assert_awaited_once()
    mock_cursor.execute.side_effect = None


def test_PT03(client):
    """
    Test Case: Attempt to create a pin without a valid token
    Expected: 401 Unauthorized
    """
    app.dependency_overrides.pop(get_current_user, None)
    test_payload = {
        "title": "PT03 Title",
    }

    response = client.post("/api/v1/pins/", json=test_payload)

    assert response.status_code == 401


def test_PT04(client, mock_cursor):
    """
    Test Case: Fetch an existing pin by its valid ID
    Expected: 200 OK and the Pin data
    """
    fake_time = datetime.now(timezone.utc)

    mock_cursor.fetchone.return_value = {
        "pin_id": 1,
        "author": "PT_Username",
        "title": "Fetched Title",
        "body": "Fetched Body",
        "image_link": "https://example.com/fetched.png",
        "created_at": fake_time,
    }

    response = client.get("/api/v1/pins/1")

    assert response.status_code == 200
    data = response.json()
    assert data["pin_id"] == 1
    assert data["author"] == "PT_Username"
    assert data["title"] == "Fetched Title"


def test_PT05(client, mock_cursor):
    """
    Test Case: Return error when fetching a non-existent pin ID
    Expected: 404 Not Found
    """
    mock_cursor.fetchone.return_value = None

    response = client.get("/api/v1/pins/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Pin with ID 999 not found."}
