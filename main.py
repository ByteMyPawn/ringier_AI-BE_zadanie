import requests
import openai
from fastapi import FastAPI
import dotenv
import os

# Load environment variables from.env file
dotenv.load_dotenv()

# key from OpenWeather API
API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()


def read_root():
    return {"message": "Welcome to the Weather API!"}


@app.get("/weather/{city}")
def get_weather(city: str):
    api_key = API_KEY
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
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
