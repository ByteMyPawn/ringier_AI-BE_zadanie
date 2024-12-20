from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import os
import dotenv
import requests
from utils.article_generator import WeatherArticle
from utils.language_utils import get_user_preferred_language, validate_language_input
from utils.style_utils import get_user_preferred_style, validate_style_input

router = APIRouter()
dotenv.load_dotenv()
host = os.getenv("HOST_ADDRESS")

# Use OAuth2PasswordBearer to extract the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.get("/generate-forecast/{city}", tags=["Main functions"],
            summary="Generate weather forecast article for tomorrow")
def generate_article(
    city: str,
    style: str = Query(None),
    lang: str = Query(None, max_length=2),
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

    # Get user's preferred language and style if not provided
    if lang is None:
        lang = get_user_preferred_language(username)
    if style is None:
        style = get_user_preferred_style(username)

    # Validate language
    language_info = validate_language_input(lang)
    language_fullname = language_info[lang]

    # Validate style and get its description
    style_info = validate_style_input(style)
    style_description = style_info[style]
    # Call the existing weather endpoint
    weather_response = requests.get(f"http://{host}:8000/weather/{city}", headers={
        "Authorization": f"Bearer {token}"
    })

    if weather_response.status_code != 200:
        try:
            error_detail = weather_response.json().get("detail", weather_response.text)
        except ValueError:
            error_detail = weather_response.text

        raise HTTPException(
            status_code=weather_response.status_code,
            detail={"Failed to retrieve weather data": error_detail}
        )

    weather_data = weather_response.json()

    # Instantiate the WeatherArticle class with style description
    article_generator = WeatherArticle(
        weather_data, lang, language_fullname, style, style_description)

    # Generate the article
    article_generator.generate()

    # Return the article as a dictionary
    return article_generator.to_dict()
