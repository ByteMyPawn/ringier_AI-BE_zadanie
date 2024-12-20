from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from auth import get_current_user, login

from models import Token

router = APIRouter()


@router.post("/token", response_model=Token, include_in_schema=False)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends()):
    return await login(form_data)
