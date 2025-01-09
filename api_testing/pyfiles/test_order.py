import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from dbop import router

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

# Test GET /order

def test_get_order_success(mock_db):
    mock_db.fetchall.return_value = [
        (1, "new", [{"food_name": "Food1", "food_price": 10.0}]),
        (2, "prepare", [{"food_name": "Food2", "food_price": 20.0}]),
    ]
    mock_db.description = [
        ("order_number",),
        ("status",),
        ("fooditems",),
    ]
    with patch("dbop.get_current_user", return_value=1):
        response = client.get("/order")
        assert response.status_code == 200
        assert response.json() == [
            {
                "order_number": 1,
                "status": "new",
                "fooditems": [{"food_name": "Food1", "food_price": 10.0}],
            },
            {
                "order_number": 2,
                "status": "prepare",
                "fooditems": [{"food_name": "Food2", "food_price": 20.0}],
            },
        ]

def test_get_order_failure(mock_db):
    mock_db.execute.side_effect = Exception("Mock error")
    with patch("dbop.get_current_user", return_value=1):
        response = client.get("/order")
        assert response.status_code == 500
        assert "Failed to fetch menus" in response.json()["detail"]

# Test GET /history

def test_get_order_history_success(mock_db):
    mock_db.fetchall.return_value = [
        (1, "complete", [{"food_name": "Food1", "food_price": 10.0}]),
        (2, "cancelled", [{"food_name": "Food2", "food_price": 20.0}]),
    ]
    mock_db.description = [
        ("order_number",),
        ("status",),
        ("fooditems",),
    ]
    with patch("dbop.get_current_user", return_value=1):
        response = client.get("/history")
        assert response.status_code == 200
        assert response.json() == [
            {
                "order_number": 1,
                "status": "complete",
                "fooditems": [{"food_name": "Food1", "food_price": 10.0}],
            },
            {
                "order_number": 2,
                "status": "cancelled",
                "fooditems": [{"food_name": "Food2", "food_price": 20.0}],
            },
        ]

def test_get_order_history_failure(mock_db):
    mock_db.execute.side_effect = Exception("Mock error")
    with patch("dbop.get_current_user", return_value=1):
        response = client.get("/history")
        assert response.status_code == 500
        assert "Failed to fetch menus" in response.json()["detail"]

# Test PUT /order/update-status

def test_update_order_status_success(mock_db):
    mock_db.fetchone.return_value = (1, "completed")
    with patch("dbop.get_current_user", return_value=1):
        response = client.put(
            "/order/update-status",
            json={"order_number": 1, "status": "completed"},
        )
        assert response.status_code == 200
        assert response.json() == {
            "message": "Order status updated successfully!",
            "order_number": 1,
            "new_status": "completed",
        }

def test_update_order_status_failure(mock_db):
    mock_db.fetchone.return_value = None
    with patch("dbop.get_current_user", return_value=1):
        response = client.put(
            "/order/update-status",
            json={"order_number": 999, "status": "completed"},
        )
        assert response.status_code == 404
        assert "Order not found" in response.json()["detail"]
