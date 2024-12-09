import os
import requests
import json
from fastapi import FastAPI, HTTPException

app = FastAPI()

# Load the RapidAPI key from the environment
rapid_API_KEY = os.getenv("RAPID_API_KEY")

url_gpt = "https://cheapest-gpt-4-turbo-gpt-4-vision-chatgpt-openai-ai-api.p.rapidapi.com/v1/chat/completions"


@app.post("/generate-article/")
def generate_article(data: dict, style: str = "factual"):
    weather_data = data

    # Construct the query based on the selected style
    if style == "factual":
        style_description = "factual, informative, and objective"
    elif style == "sensational":
        style_description = "sensational, engaging, and dramatic"
    else:
        raise HTTPException(status_code=400, detail="Invalid style selected")

    query = f"Generate a {style_description} weather article with a title, lead, and body based on the following data: {weather_data}"

    payload = {
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ],
        "model": "gpt-4o",
        "max_tokens": 2000,
        "temperature": 0.9
    }
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": rapid_API_KEY,
        "X-RapidAPI-Host": "cheapest-gpt-4-turbo-gpt-4-vision-chatgpt-openai-ai-api.p.rapidapi.com"
    }

    response = requests.post(url_gpt, json=payload, headers=headers)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="Error communicating with the API")

    try:
        clean_response = response.json()["choices"][0]["message"]["content"]
    except KeyError:
        raise HTTPException(status_code=500,
                            detail="Unexpected response format from the API")

    # Directly return the clean response without unnecessary transformations
    return {"article": clean_response}


if __name__ == "__main__":
    example_data = {
        "coord": {
            "lon": 18.739,
            "lat": 49.223
        },
        "weather": [
            {
                "id": 804,
                "main": "Clouds",
                "description": "overcast clouds",
                "icon": "04n"
            }
        ],
        "base": "stations",
        "main": {
            "temp": 2.99,
            "feels_like": -0.68,
            "temp_min": 2.56,
            "temp_max": 3.77,
            "pressure": 1018,
            "humidity": 83,
            "sea_level": 1018,
            "grnd_level": 955
        },
        "visibility": 10000,
        "wind": {
            "speed": 4.12,
            "deg": 70
        },
        "clouds": {
            "all": 100
        },
        "dt": 1733761301,
        "sys": {
            "type": 2,
            "id": 2037021,
            "country": "SK",
            "sunrise": 1733725703,
            "sunset": 1733755615
        },
        "timezone": 3600,
        "id": 3056508,
        "name": "Žilina",
        "cod": 200
    }

    # Specify the style when calling the function
    print(generate_article(data=example_data, style="sensational"))
