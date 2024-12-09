#fmt: off
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.db_conn import get_db_connection
from timezonefinder import TimezoneFinder
import pytz
import dotenv
from fastapi.responses import JSONResponse
import requests
from datetime import datetime
from fastapi import APIRouter
#fmt: on

tf = TimezoneFinder()

router = APIRouter()

os.environ.pop("POSTGRES_USER", None)
os.environ.pop("POSTGRES_PASSWORD", None)

dotenv.load_dotenv()

postgres_user = os.getenv("POSTGRES_USER")

postgres_password = os.getenv("POSTGRES_PASSWORD")

host = os.getenv("HOST_ADDRESS")

# Database connection parameters
conn = get_db_connection()

cursor = conn.cursor()

# Query the database to get city data
cursor.execute("SELECT name, latitude, longitude FROM supported_cities;")

# Fetch all rows from the query result
rows = cursor.fetchall()

# Convert the result into a dictionary (city name as key)
city_coordinates = {
    row[0].lower(): {
        "lat": row[1],
        "lon": row[2]} for row in rows}

# Close the cursor and connection
cursor.close()
conn.close()


# key from OpenWeather API
API_KEY = os.getenv("WEATHER_API_KEY")

# Dictionary mapping city names to their coordinates
city_coordinates = {
    "zilina": {"lat": 49.223, "lon": 18.739},
    "bratislava": {"lat": 48.148, "lon": 17.107},
    "praha": {"lat": 50.0755, "lon": 14.4378}
}


def try_request_openWeather_api(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        return JSONResponse(
            content={
                "message": "Weather API not responding, try again later",
                "details": str(e)},
            status_code=503  # Service Unavailable
        )


@router.get("/weather/{city}")
def get_weather(city: str):
    # Retrieve the coordinates for the given city
    coordinates = city_coordinates.get(city)
    if not coordinates:
        return {"error": "City not available, try: " +
                ', '.join(city_coordinates.keys())}

    lat = coordinates["lat"]
    lon = coordinates["lon"]
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    return try_request_openWeather_api(url)


@router.get("/weather/{city}/{date}")
def get_weather_history(
        city: str, date: str):
    # Retrieve the coordinates for the given city
    coordinates = city_coordinates.get(city)
    if not coordinates:
        return {"error": "City not available, try: " +
                ', '.join(city_coordinates.keys())}

    lat = coordinates["lat"]
    lon = coordinates["lon"]

    # Parse the date string
    try:
        date_obj = datetime.strptime(date, "%d-%m-%Y")
    except ValueError:
        return {"error": "Invalid date format. Use DD-MM-YYYY."}

    # Determine the timezone based on the latitude and longitude
    timezone_str = tf.timezone_at(lat=lat, lng=lon)

    if not timezone_str:
        return {"error": "Could not determine timezone for the given coordinates."}

    timezone = pytz.timezone(timezone_str)

    # Set the time to 12:00:00 and localize to the city's timezone
    date_obj = timezone.localize(date_obj.replace(hour=12, minute=0, second=0))

    # Convert to Unix timestamp
    unixtime = int(date_obj.timestamp())

    # Construct the URL with the calculated unixtime
    url = f"https://api.openweathermap.org/data/3.0/onecall/timemachine?lat={lat}&lon={lon}"
    url += f"&dt={unixtime}"
    url += f"&appid={API_KEY}"
    url += "&units=metric"
    return try_request_openWeather_api(url)
