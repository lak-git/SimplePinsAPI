import jwt
import time
import uuid
from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM
from app.core.security import (
    hash_password,
    create_access_token,
    create_refresh_token,
)


"""
/api/v1/oauth/token
"""


def test_AT01(client, mock_cursor):
    """
    Test Case: Obtain/login with valid credentials to receive tokens
    Expected: 200 OK and token payload
    """
    valid_password = "AT01_Password"
    hashed_pw = hash_password(valid_password)
    fake_uuid = uuid.uuid4().bytes

    mock_cursor.fetchone.return_value = {"UserUUID": fake_uuid, "Password": hashed_pw}
    form_data = {"username": "AT01_Username", "password": valid_password}
    response = client.post("/api/v1/oauth/token", data=form_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    assert mock_cursor.execute.call_count == 3


def test_AT02(client, mock_cursor):
    """
    Test Case: Reject login with incorrect password
    Expected: 401 Unauthorized
    """
    real_password = "AT02_Password_Real"
    hashed_pw = hash_password(real_password)

    mock_cursor.fetchone.return_value = {
        "UserUUID": b"AT02_UUID",
        "Password": hashed_pw,
    }

    form_data = {"username": "AT02_Username", "password": "AT02_Password_Wrong"}
    response = client.post("/api/v1/oauth/token", data=form_data)

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password."}


def test_AT03(client, mock_cursor):
    """
    Test Case: Reject login if the username does not exist
    Expected: 401 Unauthorized
    """
    mock_cursor.fetchone.return_value = None

    form_data = {"username": "AT03_Username", "password": "AT03_Password"}
    response = client.post("/api/v1/oauth/token", data=form_data)

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password."}


"""
/api/v1/oauth/refresh
"""


def test_AT04(client, mock_cursor):
    """
    Test Case: Issue new tokens when a valid refresh token is provided
    Expected: 200 OK and new tokens
    """
    valid_uuid = str(uuid.uuid4())
    valid_refresh = create_refresh_token(valid_uuid)

    mock_cursor.fetchone.return_value = {"IsRevoked": False}
    response = client.post(
        "/api/v1/oauth/refresh", json={"refresh_token": valid_refresh}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()


def test_AT05(client, mock_cursor):
    """
    Test Case: Reject request if an ACCESS token is passed instead of a REFRESH token
    Expected: 401 Unauthorized
    """
    valid_uuid = str(uuid.uuid4())
    access_token = create_access_token(valid_uuid)

    response = client.post(
        "/api/v1/oauth/refresh", json={"refresh_token": access_token}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token type"}


def test_AT06(client, mock_cursor):
    """
    Test Case: Reject mathematically expired refresh tokens
    Expected: 401 Unauthorized
    """
    expired_payload = {
        "user_uuid": str(uuid.uuid4()),
        "type": "refresh",
        "exp": int(time.time()) - 3600,
    }
    expired_token = jwt.encode(expired_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    response = client.post(
        "/api/v1/oauth/refresh", json={"refresh_token": expired_token}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Refresh Token has expired."}


def test_AT07(client, mock_cursor):
    """
    Test Case: Reject tokens that are valid mathematically but revoked in the database
    Expected: 401 Unauthorized
    """
    valid_uuid = str(uuid.uuid4())
    valid_refresh = create_refresh_token(valid_uuid)
    mock_cursor.fetchone.return_value = {"IsRevoked": True}

    response = client.post(
        "/api/v1/oauth/refresh", json={"refresh_token": valid_refresh}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Refresh Token is revoked."}
