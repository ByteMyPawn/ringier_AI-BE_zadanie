from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from auth import get_current_user, login

from models import Token, UserInDB

router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends()):
    return await login(form_data)


@router.get("/users/me", response_model=UserInDB)
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return current_user
