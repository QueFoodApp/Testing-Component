import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from api_testing.pyfiles.dbop import router
from api_testing.pyfiles.dbop import UpdateMenuAvailability, UpdateMenuByCategory

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

# Test GET /menus

def test_get_menus_success(mock_db):
    mock_db.fetchall.return_value = [("Category1",), ("Category2",)]
    mock_db.description = [("category",)]
    with patch("dbop.get_current_user", return_value=1):
        response = client.get("/menus")
        assert response.status_code == 200
        assert response.json() == [
            {"category": "Category1"},
            {"category": "Category2"}
        ]

def test_get_menus_failure(mock_db):
    mock_db.execute.side_effect = Exception("Mock error")
    with patch("dbop.get_current_user", return_value=1):
        response = client.get("/menus")
        assert response.status_code == 500
        assert "Failed to fetch menus" in response.json()["detail"]

# Test GET /menus/food

def test_get_menus_food_success(mock_db):
    mock_db.fetchall.return_value = [
        ("Food1", 10.0, "Available"),
        ("Food2", 15.0, "Unavailable")
    ]
    mock_db.description = [("food_name",), ("food_price",), ("availability",)]
    with patch("dbop.get_current_user", return_value=1):
        response = client.get("/menus/food", params={"category": "Category1"})
        assert response.status_code == 200
        assert response.json() == [
            {"food_name": "Food1", "food_price": 10.0, "availability": "Available"},
            {"food_name": "Food2", "food_price": 15.0, "availability": "Unavailable"}
        ]

def test_get_menus_food_failure(mock_db):
    mock_db.execute.side_effect = Exception("Mock error")
    with patch("dbop.get_current_user", return_value=1):
        response = client.get("/menus/food", params={"category": "Category1"})
        assert response.status_code == 500
        assert "Failed to fetch menus" in response.json()["detail"]

# Test PUT /menus/availability

def test_update_menu_availability_success(mock_db):
    mock_db.fetchone.return_value = ("Food1",)
    with patch("dbop.get_current_user", return_value=1):
        response = client.put(
            "/menus/availability",
            json={
                "category": "Category1",
                "food_name": "Food1",
                "availability": "Available"
            }
        )
        assert response.status_code == 200
        assert response.json() == {
            "message": "Menu availability updated successfully!",
            "food_name": "Food1",
            "new_availability": "Available"
        }

def test_update_menu_availability_failure(mock_db):
    mock_db.fetchone.return_value = None
    with patch("dbop.get_current_user", return_value=1):
        response = client.put(
            "/menus/availability",
            json={
                "category": "Category1",
                "food_name": "NonExistentFood",
                "availability": "Available"
            }
        )
        assert response.status_code == 404
        assert "No food items found" in response.json()["detail"]

# Test PUT /menus/update-availability

def test_update_menu_by_category_success(mock_db):
    mock_db.fetchall.return_value = [("Food1",), ("Food2",)]
    with patch("dbop.get_current_user", return_value=1):
        response = client.put(
            "/menus/update-availability",
            json={
                "category": "Category1",
                "availability": "Unavailable"
            }
        )
        assert response.status_code == 200
        assert response.json() == {
            "message": "Menu availability updated successfully!",
            "updated_food_names": ["Food1", "Food2"],
            "new_availability": "Unavailable"
        }

def test_update_menu_by_category_failure(mock_db):
    mock_db.fetchall.return_value = []
    with patch("dbop.get_current_user", return_value=1):
        response = client.put(
            "/menus/update-availability",
            json={
                "category": "NonExistentCategory",
                "availability": "Unavailable"
            }
        )
        assert response.status_code == 404
        assert "No food items found" in response.json()["detail"]
