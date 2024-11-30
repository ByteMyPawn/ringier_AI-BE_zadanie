import requests
import openai
from fastapi import FastAPI
import dotenv
import os

from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordRequestForm
from auth import login, get_current_user
from models import Token, UserInDB

# Load environment variables from.env file
dotenv.load_dotenv()

app = FastAPI()


@app.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends()):
    return await login(form_data)


@app.get("/users/me", response_model=UserInDB)
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return current_user


# Load environment variables from.env file
dotenv.load_dotenv()

# key from OpenWeather API
API_KEY = os.getenv("OPENAI_API_KEY")


def read_root():
    return {"message": "Welcome to the Weather API!"}


@app.get("/weather/{city}")
def get_weather(city: str):
    api_key = API_KEY
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    return response.json()


@app.post("/generate-article/")
def generate_article(data: dict):
    weather_data = data["weather_data"]
    style = data["style"]  # "factual" or "dramatic"

    prompt = f"Generate a {style} weather article: {weather_data}"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=300
    )
    return {"article": response.choices[0].text.strip()}
