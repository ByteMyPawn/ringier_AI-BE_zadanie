#fmt: off
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from utils.db_conn import get_db_connection
from passlib.context import CryptContext
#fmt: on
router = APIRouter()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(user: UserCreate):
    # Hash the password
    hashed_password = hash_password(user.password)

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the username or email already exists
    cursor.execute(
        "SELECT * FROM users WHERE username = %s OR email = %s",
        (user.username,
         user.email))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists")

    # Insert the new user into the database
    cursor.execute(
        "INSERT INTO users (username, hashed_password, email) VALUES (%s, %s, %s)",
        (user.username, hashed_password, user.email)
    )
    conn.commit()

    # Close the cursor and connection
    cursor.close()
    conn.close()

    return {"message": "User created successfully"}
