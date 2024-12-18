#fmt: off
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from models import UserInDB, Token
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, status
from typing import Optional
from datetime import datetime, timedelta
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.db_conn import get_db_connection
#fmt: on

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def fake_hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# Update the get_user function to query the database
def get_user(username: str) -> Optional[UserInDB]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT u.username, u.hashed_password, u.role, l.id AS preferred_language_id, l.name AS preferred_language_name, l.code AS preferred_language_code,
               s.id AS preferred_style_id, s.name AS preferred_style_name
        FROM users u
        LEFT JOIN languages l ON u.preferred_language_id = l.id
        LEFT JOIN styles s ON u.preferred_style_id = s.id
        WHERE u.username = %s
        """, (username,))

    user_record = cursor.fetchone()
    cursor.close()
    conn.close()

    if user_record:
        return UserInDB(
            username=user_record[0],
            hashed_password=user_record[1],
            role=user_record[2],  # Include the role here
            preferred_language={
                "id": user_record[3],
                "name": user_record[4],
                "code": user_record[5]},
            preferred_style={"id": user_record[6], "name": user_record[7]}
        )
    return None


# Update the authenticate_user function to use the updated get_user
def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str = Depends(oauth2_scheme)) -> UserInDB:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Fetch user from the real database
        user = get_user(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found",
            )
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Login route
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    print(f"Attempting to authenticate user: {form_data.username}")
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        print(f"Authentication failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    print(f"User '{user.username}' is authenticated.")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# User verification
async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Fetch user from the database
        user = get_user(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found",
            )
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
