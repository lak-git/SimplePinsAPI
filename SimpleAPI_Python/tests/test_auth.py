from app.core.security import JWT_ACCESS_TOKEN_EXPIRE_MINUTES


# Tests arranged using AAA Model


def test_AT01(client, mock_cursor):
    """
    Test Case: Register a new user with valid credentials
    Expected: 201 Created and a token payload
    """
    # 1. ARRANGE
    mock_cursor.fetchone.return_value = None
    test_payload = {"username": "AT01_Username", "password": "AT01_Password"}
    # 2. ACT
    response = client.post("/api/v1/users/", json=test_payload)
    # 3. ASSERT
    assert response.status_code == 201

    data = response.json()
    assert "user_id" in data
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["expires_in"] == JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

    # To check wheter DB was executed 3 times: SELECT - Check, INSERT - User, INSERT - Refresh
    assert mock_cursor.execute.call_count == 3


def test_AT02(client, mock_cursor):
    """
    Test Case: Reject registration if username already exists
    Expected: 409 Conflict
    """
    mock_cursor.fetchone.return_value = {"UserUUID": b"AT02_UUID"}
    test_payload = {"username": "AT02_Username", "password": "AT02_Password"}

    response = client.post("/api/v1/users/", json=test_payload)

    assert response.status_code == 409
    assert response.json() == {"detail": "User already registered"}
