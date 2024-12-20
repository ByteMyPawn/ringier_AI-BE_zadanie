#fmt: off
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import requests
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from dotenv import load_dotenv, set_key
from auth import authenticate_user, create_access_token
from models import Token
#fmt: on

os.environ.pop("USERNAME", None)
os.environ.pop("PASSWORD", None)
os.environ.pop("JWT_TOKEN", None)
load_dotenv()

username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")

router = APIRouter()

host = os.getenv("HOST_ADDRESS")


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login", response_model=Token, tags=["General"], summary="Login")
async def login_for_access_token(login_request: LoginRequest):
    user = authenticate_user(login_request.username, login_request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


def login(username, password):
    print(f"Attempting to authenticate user: {username}")
    access_token = os.getenv("JWT_TOKEN")
    print(access_token)
    headers = {"Authorization": f"Bearer {access_token}"}
    example_response = requests.get(
        f"http://{host}:8000/login", headers=headers)

    if example_response.status_code == 200:
        print("Response from /login endpoint:")
        try:
            print(example_response.json())
        except requests.exceptions.JSONDecodeError:
            print("Response is not in JSON format.")
        return True
    elif example_response.status_code == 401:
        print(
            f"Failed to access /login endpoint: {example_response.status_code} ...\nTry to access new one ...")

        data = {"username": username, "password": password}
        print(data)
        token_response = requests.post(f"http://{host}:8000/token", data=data)

        if token_response.status_code == 200:
            access_token = token_response.json().get("access_token")
            print(f"Access token: {access_token}")
            headers = {"Authorization": f"Bearer {access_token}"}
            example_response = requests.get(
                f"http://{host}:8000/login", headers=headers)

            if example_response.status_code == 200:
                print("Response from /login endpoint:")
                try:
                    print(example_response.json())
                except requests.exceptions.JSONDecodeError:
                    print("Response is not in JSON format.")
                set_key(".env", "USERNAME", username)
                set_key(".env", "PASSWORD", password)
                set_key(".env", "JWT_TOKEN", access_token)
                return True
            else:
                print(
                    f"Failed to access /login endpoint: {example_response.status_code}")
                try:
                    print(example_response.json())
                except requests.exceptions.JSONDecodeError:
                    print("Response is not in JSON format.")
                return False
        else:
            proceed_or_not = input(
                "Failed to login, do you want to try again? (Y/n): ")
            if proceed_or_not.lower() == "y" or proceed_or_not.lower() == "":
                new_login = input("Enter your username:")
                new_password = input("Enter new password: ")
                login(new_login, new_password)
            else:
                print("Failed to obtain token")
                try:
                    print(token_response.json())
                except requests.exceptions.JSONDecodeError:
                    print("Response is not in JSON format.")
                print("Exiting...")
                return False
    else:
        print("Failed to obtain token")
        try:
            print(example_response.json())
        except requests.exceptions.JSONDecodeError:
            print("Response is not in JSON format.")
        return False
