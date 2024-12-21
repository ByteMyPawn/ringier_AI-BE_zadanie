#fmt: off
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.db_conn import get_db_connection
from utils.language_utils import get_user_preferred_language, validate_language_input
from timezonefinder import TimezoneFinder
import pytz
import dotenv
from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
import requests
from datetime import datetime
import json
from jose import JWTError, jwt
#fmt: on

tf = TimezoneFinder()

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

dotenv.load_dotenv()

# Database connection parameters
conn = get_db_connection()

cursor = conn.cursor()

# Query the database to get city data
cursor.execute("SELECT name, latitude, longitude, id FROM supported_cities;")

# Fetch all rows from the query result
rows = cursor.fetchall()

# Convert the result into a dictionary (city name as key)
city_coordinates_and_id = {
    row[0].lower(): {
        "lat": row[1],
        "lon": row[2],
        "id": row[3]
    } for row in rows}

# Close the cursor and connection
cursor.close()
conn.close()


def get_city_coordinates(city: str):
    """Retrieve the coordinates for the given city."""
    coordinates = city_coordinates_and_id.get(city.lower())
    if not coordinates:
        raise HTTPException(
            status_code=400,
            detail={"error": "City not available, try: " +
                    ', '.join(city_coordinates_and_id.keys())}
        )
    return coordinates["lat"], coordinates["lon"], coordinates["id"]


# key from OpenWeather API
API_KEY = os.getenv("WEATHER_API_KEY")


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


@router.get("/weather/{city}", include_in_schema=False)
def get_weather(
    city: str,
    token: str = Depends(oauth2_scheme)
):
    # Decode the JWT token to get the username
    try:
        token_data = jwt.decode(
            token,
            os.getenv("SECRET_KEY"),
            algorithms=["HS256"]
        )
        username = token_data.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    lat, lon, city_id = get_city_coordinates(city)

    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    return try_request_openWeather_api(url)


@router.get("/weather/{city}/{date}", tags=["Main functions"],
            summary="Get weather history for a specific date")
def get_weather_history(
        city: str, date: str, lang: str = Query(None, max_length=2),
        token: str = Depends(oauth2_scheme)):
    # Decode the JWT token to get the username
    try:
        token_data = jwt.decode(
            token,
            os.getenv("SECRET_KEY"),
            algorithms=["HS256"])
        # Assuming 'sub' contains the username
        username = token_data.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_preferred_lang = get_user_preferred_language(username)

    # Use the preferred language from the database if lang is not set
    if lang is None:
        lang = user_preferred_lang

    lat, lon, city_id = get_city_coordinates(city)

    # Validate the language input
    validate_language_input(lang)

    # Parse the date string
    try:
        date_obj = datetime.strptime(date, "%d-%m-%Y")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"error": "Invalid date format. Use DD-MM-YYYY."})

    # Validate that the date is not earlier than 01-01-1979
    min_date = datetime.strptime("01-01-1979", "%d-%m-%Y")
    if date_obj < min_date:
        raise HTTPException(
            status_code=400,
            detail={"error": "Date must be on or after 01-01-1979."})

    # Get today's date at 0:00 (midnight)
    today_midnight = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0)

    if date_obj > today_midnight:
        raise HTTPException(
            status_code=400,
            detail={"error": "Date must be on or before yesterday."})

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Query the translations table for the given language code if not "EN"
        key_translations = {}
        value_translations = {}
        if lang != "EN":
            cursor.execute(
                "SELECT key_name, translation FROM key_translations WHERE language_code = %s", (lang,))
            key_translations = {str(key): str(value)
                                for key, value in cursor.fetchall()}
            cursor.execute(
                "SELECT value_name, translation FROM value_translations WHERE language_code = %s", (lang,))
            value_translations = {str(original): str(translated)
                                  for original, translated in cursor.fetchall()}

        # Check if the weather data is already in the database
        cursor.execute(
            "SELECT weather_data FROM weather_history WHERE city_id = (SELECT id FROM supported_cities WHERE LOWER(name) = %s) AND date = %s",
            (city.lower(), date_obj))
        result = cursor.fetchone()

        if result:
            # Data found in the database, return it
            weather_data = result[0]

        else:
            # Determine the timezone based on the latitude and longitude
            timezone_str = tf.timezone_at(lat=lat, lng=lon)

            if not timezone_str:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "Could not determine timezone for the given coordinates."})

            timezone = pytz.timezone(timezone_str)

            # Set the time to 12:00:00 and localize to the city's timezone
            date_obj = timezone.localize(
                date_obj.replace(
                    hour=12, minute=0, second=0))

            # Convert to Unix timestamp
            unixtime = int(date_obj.timestamp())

            # Construct the URL with the calculated unixtime
            url = f"https://api.openweathermap.org/data/3.0/onecall/timemachine?lat={lat}&lon={lon}"
            url += f"&dt={unixtime}"
            url += f"&appid={API_KEY}"
            url += "&units=metric"
            response = try_request_openWeather_api(url)

            if isinstance(response, dict):
                # Store the response in the database
                response_json = json.dumps(response)
                cursor.execute(
                    "INSERT INTO weather_history (city_id, date, weather_data) VALUES ((SELECT id FROM supported_cities WHERE id = %s), %s, %s)",
                    (city_id, date_obj, response_json))
                conn.commit()

            weather_data = response

        # Replace keys in the response with translations if lang is not "EN"
        if lang != "EN" and isinstance(weather_data, dict):
            weather_data = translate_response(
                weather_data, key_translations, value_translations)

    finally:
        cursor.close()
        conn.close()

    return weather_data


def translate_response(response: dict, key_translations: dict,
                       value_translations: dict) -> dict:
    translated_response = {}
    for key, value in response.items():
        # Translate the key
        translated_key = key_translations.get(key, key)
        if isinstance(value, dict):
            # Recursively translate subkeys and values
            translated_response[translated_key] = translate_response(
                value, key_translations, value_translations)
        elif isinstance(value, list):
            # If the value is a list, translate each item if it's a dictionary
            translated_response[translated_key] = [
                translate_response(
                    item, key_translations, value_translations) if isinstance(
                    item, dict) else value_translations.get(item, item)
                for item in value
            ]
        else:
            # Translate the value
            translated_response[translated_key] = value_translations.get(
                value, value)

    return translated_response
