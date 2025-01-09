import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from api_testing.pyfiles.dbop import router, User, Login

# Set up FastAPI TestClient
client = TestClient(router)

# Mock database connection fixture
@pytest.fixture
def mock_db():
    with patch("psycopg2.connect") as mock_connect:
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        yield mock_cursor

# Test registration endpoint

def test_register_success(mock_db):
    # Mock database behavior for successful registration
    mock_db.fetchone.return_value = None  # No duplicate user
    response = client.post(
        "/register",
        json={
            "username": "test_user",
            "password": "test_pass",
            "restaurant_id": 1,
            "manager_id": 123,
        },
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User registered successfully!"

def test_register_failure(mock_db):
    # Mock database behavior for registration failure
    mock_db.execute.side_effect = Exception("Mock registration error")
    response = client.post(
        "/register",
        json={
            "username": "test_user",
            "password": "test_pass",
            "restaurant_id": 1,
            "manager_id": 123,
        },
    )
    assert response.status_code == 400
    assert "Failed to register user" in response.json()["detail"]

# Test login endpoint

def test_login_success(mock_db):
    # Mock database behavior for successful login
    mock_db.fetchone.return_value = ("hashed_password", 123)  # Valid user credentials
    with patch("dbop.create_access_token") as mock_token:
        mock_token.return_value = "mocked_token"
        response = client.post(
            "/login",
            json={"username": "test_user", "password": "hashed_password"},
        )
        assert response.status_code == 200
        assert response.json()["access_token"] == "mocked_token"
        assert response.json()["token_type"] == "bearer"

def test_login_failure_invalid_credentials(mock_db):
    # Mock database behavior for invalid credentials
    mock_db.fetchone.return_value = None
    response = client.post(
        "/login",
        json={"username": "test_user", "password": "wrong_password"},
    )
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]

def test_login_failure_db_error(mock_db):
    # Mock database behavior for login error
    mock_db.execute.side_effect = Exception("Mock login error")
    response = client.post(
        "/login",
        json={"username": "test_user", "password": "hashed_password"},
    )
    assert response.status_code == 400
    assert "Login failed" in response.json()["detail"]
