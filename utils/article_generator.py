import requests
from fastapi import HTTPException
import os
import json

# Load the RapidAPI key from the environment
rapid_API_KEY = os.getenv("RAPID_API_KEY")
url_API_gpt = "https://cheapest-gpt-4-turbo-gpt-4-vision-chatgpt-openai-ai-api.p.rapidapi.com/v1/chat/completions"


class WeatherArticle:
    def __init__(self, weather_data: dict, language_code: str = "EN", language_name: str = "English", style: str = "factual",
                 style_description: str = "Factual and concise writing style focused on clear, objective, and structured content. Uses a formal tone, active voice, and technical precision, with brevity and no unnecessary elaboration or repetition."):
        self.weather_data = weather_data
        self.style = style
        self.style_description = style_description
        self.language_code = language_code
        self.language_name = language_name
        self.title = ""
        self.lead = ""
        self.body = ""

    def generate(self):
        # Construct the query with language and request a dictionary format
        query = (
            f"Generate a {self.style} weather forecast article for tommorow in {self.language_name} ({self.language_code}) language. Style description: {self.style_description}. "
            f"with a title, lead, and body based on the following data: {self.weather_data}. Use degrees rounded without decimals and wind direction in cardinal directions) "
            "Return the response as a JSON-like dictionary with keys 'title' (maximum 160 characters), 'lead' (minimum 160 characters), and 'body' (minimum 500 characters)."
        )

        # Call the LLM API to generate the article
        response = self._call_llm_api(query)

        # Parse the response to extract title, lead, and body
        self._parse_response(response)

    def _call_llm_api(self, query: str) -> dict:
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

        response = requests.post(url_API_gpt, json=payload, headers=headers)

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error communicating with the API: {response.text}"
            )

        return response.json()

    def _parse_response(self, response: dict):
        try:
            content = response["choices"][0]["message"]["content"]
            # Remove the surrounding code block markers if present
            if content.startswith("```json") and content.endswith("```"):
                content = content[7:-3].strip()
            # Parse the content as a dictionary
            article_dict = json.loads(content)
            self.title = article_dict.get("title", "")
            self.lead = article_dict.get("lead", "")
            self.body = article_dict.get("body", "")
        except (KeyError, IndexError, json.JSONDecodeError):
            raise HTTPException(status_code=500,
                                detail="Unexpected response format from the API")

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "perex": self.lead,
            "body": self.body
        }
