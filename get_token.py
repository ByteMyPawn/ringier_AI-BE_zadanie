from dotenv import load_dotenv
import os
import requests

load_dotenv()

host = os.getenv("HOST_ADDRESS")


def get_token():
    # Logic to obtain a token
    token_response = requests.post(f"http://{host}:8000/token", data={
        "username": os.getenv("USERNAME"),
        "password": os.getenv("PASSWORD")
    })
    if token_response.status_code == 200:
        return token_response.json().get("access_token")
    else:
        raise Exception("Failed to obtain token")


if __name__ == "__main__":
    try:
        token = get_token()
        print(f"Access token: {token}")
    except Exception as e:
        print(str(e))
