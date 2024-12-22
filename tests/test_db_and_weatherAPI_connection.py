#fmt: off
import os
import sys
from fastapi.testclient import TestClient
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from main import app  # Ensure this is the correct import for your FastAPI app
import dotenv
import json
import httpx
dotenv.load_dotenv()


def test_update_preferences():
    client = TestClient(app)

    # First, authenticate to get a token
    response = client.post("/token", data={"username": os.getenv('USERNAME'), "password": os.getenv('PASSWORD')})
    assert response.status_code == 200
    token = response.json().get("access_token")

    # Set the authorization header
    headers = {"Authorization": f"Bearer {token}"}

    # Define the preferences to update
    preferences = {
        "preferred_language": "EN",
        "preferred_style": "factual"
    }

    # Send a PUT request to update preferences
    response = client.put("/users/me/preferences", json=preferences, headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Preferences updated successfully, check all preferences in get /users/me/preferences endpoint"
    assert response.json()["updated_preferences"] == {
        "preferred_language": "EN",
        "preferred_style": "factual"
    }

def test_user_management():
    client = TestClient(app)

    # Authenticate as superuser to get a token
    response = client.post("/token", data={"username": os.getenv('SUPERUSERNAME'), "password": os.getenv('SUPERUSERPASSWORD')})
    assert response.status_code == 200
    superuser_token = response.json().get("access_token")

    # Set the authorization header for superuser
    superuser_headers = {"Authorization": f"Bearer {superuser_token}"}

    # Define the new user to create
    new_user = {
        "username": "testuser",
        "password": "testpassword",
        "email": "testuser@example.com"
    }

    # Send a POST request to create a new user
    response = client.post("/users", json=new_user, headers=superuser_headers)
    assert response.status_code == 201
    assert response.json()["message"] == f"User '{new_user['username']}' created successfully"

    # Authenticate as the new user to verify creation
    response = client.post("/token", data={"username": "testuser", "password": "testpassword"})
    assert response.status_code == 200
    user_token = response.json().get("access_token")

    # Set the authorization header for the new user
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Verify the new user can access their own data
    response = client.get("/users/me", headers=user_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

    # Send a DELETE request to remove the new user using httpx
    response = httpx.request(
        method="DELETE",
        url=f"http://{os.getenv('HOST_ADDRESS')}:8000/users",  # Ensure this URL is correct for your API
        headers={
            "Authorization": f"Bearer {superuser_token}",
            "Content-Type": "application/json",
            "accept": "application/json"
        },
        content=json.dumps({"username": new_user['username']})
    )

    assert response.status_code == 200
    assert response.json()["message"] == f"User {{'username': '{new_user['username']}'}} deleted successfully"

    # Verify the user is deleted by attempting to authenticate again
    response = client.post("/token", data={"username": "testuser", "password": "testpassword"})
    assert response.status_code == 401

def test_weather_city_date_access():
    client = TestClient(app)

    # Authenticate to get a token
    response = client.post("/token", data={"username": os.getenv('USERNAME'), "password": os.getenv('PASSWORD')})
    assert response.status_code == 200
    token = response.json().get("access_token")

    # Set the authorization header
    headers = {"Authorization": f"Bearer {token}"}

    # Define the city and date for the weather request
    city = "bratislava"
    date = "07-12-2020"  

    # Send a GET request to the weather/city/date endpoint
    response = client.get(f"/weather/{city}/{date}", headers=headers)

    # Check if the endpoint is accessible and returns a successful response
    assert response.status_code == 200
    weather_data = response.json().get('data')
    assert isinstance(weather_data, list)  # Ensure it's a list
    assert len(weather_data) > 0  # Ensure the list is not empty


def test_weather_city_tomorrow_access():
    client = TestClient(app)

    # Authenticate to get a token
    response = client.post("/token", data={"username": os.getenv('USERNAME'), "password": os.getenv('PASSWORD')})
    assert response.status_code == 200
    token = response.json().get("access_token")

    # Set the authorization header
    headers = {"Authorization": f"Bearer {token}"}

    # Define the city for the weather request
    city = "bratislava"

    # Send a GET request to the weather/city endpoint
    response = client.get(f"/weather/{city}", headers=headers)

    # Check if the endpoint is accessible and returns a successful response
    assert response.status_code == 200
    weather_data = response.json()
    assert "weather" in weather_data  # Ensure the weather data is present