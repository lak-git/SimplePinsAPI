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


def test_PT06(client, mock_cursor):
    """
    Test Case: Fetch a list of pins without any filter
    Expected: 200 OK and a list of Pin data
    """
    fake_time = datetime.now(timezone.utc)
    mock_cursor.fetchall.return_value = [
        {
            "pin_id": 101,
            "author": "UserA",
            "title": "First Pin",
            "body": "Body A",
            "image_link": "linkA.png",
            "created_at": fake_time,
        },
        {
            "pin_id": 102,
            "author": "UserB",
            "title": "Second Pin",
            "body": "Body B",
            "image_link": "linkB.png",
            "created_at": fake_time,
        },
    ]

    response = client.get("/api/v1/pins/")

    assert response.status_code == 200
    data = response.json()
    assert "pins" in data
    assert len(data["pins"]) == 2
    assert data["pins"][0]["title"] == "First Pin"
    assert data["pins"][1]["author"] == "UserB"


def test_PT07(client, mock_cursor):
    """
    Test Case: Fetch a list of pins using query parameters
    Expected: 200 OK, and the generated SQL query must match the filters
    """
    mock_cursor.fetchall.return_value = []

    response = client.get(
        "/api/v1/pins/?author=TargetUser&title=Cool&sort_by=title&order=asc"
    )

    assert response.status_code == 200
    called_args = mock_cursor.execute.call_args[0]
    generated_sql = called_args[0]
    sql_parameters = called_args[1]

    assert "AND u.Username = %s" in generated_sql
    assert "AND p.Title LIKE %s" in generated_sql
    assert "ORDER BY p.Title ASC" in generated_sql
    assert sql_parameters == ("TargetUser", "%Cool%")


def test_PT08(client, mock_cursor):
    """
    Test Case: Simulate a database crash during fetching
    Expected: 500 Internal Server Error
    """
    mock_cursor.execute.side_effect = Exception("Simulated Read Error")

    response = client.get("/api/v1/pins/")

    assert response.status_code == 500
    assert response.json() == {"detail": "Database error occurred."}

    mock_cursor.execute.side_effect = None


"""
Update Pin
"""


def test_PT09(client, mock_cursor, mock_conn):
    """
    Test Case: Successfully update a pin's title (owner)
    Expected: 200 OK, updated PinResponse, and commit called
    """
    fake_time = datetime.now(timezone.utc)
    mock_cursor.fetchone.side_effect = [
        {"UserUUID": b"PT_UUID"},
        {
            "pin_id": 1,
            "author": "PT_Username",
            "title": "A Brand New Title",
            "body": "Original Body",
            "image_link": "Original Link",
            "created_at": fake_time,
        },
    ]

    test_payload = {"title": "A Brand New Title"}

    response = client.patch("/api/v1/pins/1", json=test_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "A Brand New Title"
    assert data["body"] == "Original Body"

    mock_conn.commit.assert_awaited_once()
    mock_cursor.fetchone.side_effect = None


def test_PT10(client, mock_cursor):
    """
    Test Case: Try to update a pin that doesn't exist.
    Expected: 404 Not Found.
    """
    mock_cursor.fetchone.return_value = None

    response = client.patch("/api/v1/pins/999", json={"title": "new title"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Pin with ID 999 not found."}


def test_PT11(client, mock_cursor):
    """
    Test Case: Reject update if pin belongs to another user.
    Expected: 403 Forbidden.
    """
    mock_cursor.fetchone.return_value = {"UserUUID": b"SOME_OTHER_UUID_"}

    response = client.patch("/api/v1/pins/1", json={"title": "Hacked Title"})

    assert response.status_code == 403
    assert response.json() == {"detail": "Not authorized to update this pin."}


def test_PT12(client, mock_cursor):
    """
    Test Case: Send a PATCH request with no fields to update.
    Expected: 400 Bad Request.
    """
    mock_cursor.fetchone.return_value = {"UserUUID": b"PT_UUID"}

    response = client.patch("/api/v1/pins/1", json={})

    assert response.status_code == 400
    assert response.json() == {"detail": "No valid fields provided for update."}


def test_PT13(client, mock_cursor, mock_conn):
    """
    Test Case: Simulate a DB crash during the UPDATE statement.
    Expected: 500 Internal Server Error and rollback.
    """
    mock_cursor.fetchone.return_value = {"UserUUID": b"PT_UUID"}
    mock_cursor.execute.side_effect = [None, Exception("DB Write Crash!")]

    response = client.patch("/api/v1/pins/1", json={"title": "Crash Title"})

    assert response.status_code == 500

    mock_conn.rollback.assert_awaited_once()
    mock_cursor.execute.side_effect = None


"""
Delete Pin
"""
