#fmt: off
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi import APIRouter, HTTPException, status, Depends, Body
from utils.db_conn import get_db_connection
from passlib.context import CryptContext
from auth import verify_token
from models import UserInDB, UserCreate, UserDeleteRequest

#fmt: on
router = APIRouter()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def is_superuser(user: UserInDB) -> bool:
    # Assuming there's a 'role' attribute in UserInDB that indicates the
    # user's role
    return user.role == "superuser"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


@router.post("/users", status_code=status.HTTP_201_CREATED,
             tags=["User management"], summary="Create User (SuperUser Only)")
def signup(user: UserCreate, current_user: UserInDB = Depends(verify_token)):
    if not is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create new users."
        )

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

    # Insert the new user into the database without specifying the role
    cursor.execute(
        "INSERT INTO users (username, hashed_password, email) VALUES (%s, %s, %s)",
        (user.username, hashed_password, user.email)
    )
    conn.commit()

    # Close the cursor and connection
    cursor.close()
    conn.close()

    return {"message": f"User '{user.username}' created successfully"}


@router.delete("/users", status_code=status.HTTP_200_OK,
               tags=["User management"], summary="Remove User (SuperUser Only)")
def delete_user(
    user_info: UserDeleteRequest = Body(...),
    current_user: UserInDB = Depends(verify_token)
):
    username = user_info.username
    email = user_info.email
    user_info_dict = {
        k: v for k, v in user_info.dict().items() if v is not None
    }

    if not is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete users."
        )

    if not username and not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email must be provided to delete a user."
        )

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the user exists and is a superuser
    if username and email:
        cursor.execute(
            "SELECT role FROM users WHERE username = %s AND email = %s", (username, email))
    elif username:
        cursor.execute(
            "SELECT role FROM users WHERE username = %s", (username,))
    elif email:
        cursor.execute("SELECT role FROM users WHERE email = %s", (email,))

    user_role = cursor.fetchone()
    if not user_role:
        cursor.close()
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with: {user_info_dict} not found in database"
        )

    if user_role[0] == "superuser":
        cursor.close()
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete a superuser."
        )

    # Delete the user based on username and email
    if username and email:
        cursor.execute(
            "DELETE FROM users WHERE username = %s AND email = %s", (username, email))
    elif username:
        cursor.execute("DELETE FROM users WHERE username = %s", (username,))
    elif email:
        cursor.execute("DELETE FROM users WHERE email = %s", (email,))

    conn.commit()

    # Close the cursor and connection
    cursor.close()
    conn.close()

    return {"message": f"User {user_info_dict} deleted successfully"}
