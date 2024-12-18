import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth import verify_token
from models import UserInDB
from utils.db_conn import get_db_connection
from typing import Optional

router = APIRouter()


class PreferencesUpdate(BaseModel):
    preferred_language: Optional[str] = None
    preferred_style: Optional[str] = None


@router.put("/users/me/preferences")
def update_preferences(preferences: PreferencesUpdate = None,
                       current_user: UserInDB = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch available languages from the database
    cursor.execute("SELECT id, code, name FROM languages")
    languages = {row[1].lower(): (row[0], row[2]) for row in cursor.fetchall()}

    # Fetch available styles from the database
    cursor.execute("SELECT id, name FROM styles")
    styles = {row[1].lower(): row[0] for row in cursor.fetchall()}

    bad_request_message_help = (
        f"Available languages: {list(languages.keys())}, "
        f"Available styles: {list(styles.keys())}. "
        'Example (use double quotes): {preferred_language: EN, preferred_style: factual}'
    )

    if preferences is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Request body is missing. Please provide 'preferred_language' and/or 'preferred_style'. "
                f"Help: {bad_request_message_help}"
            )
        )

    # Prepare the update query dynamically based on provided fields
    update_fields = []
    update_values = []

    if preferences.preferred_language is not None:
        preferred_language_lower = preferences.preferred_language.lower()

        if preferred_language_lower not in languages:
            available_languages = ", ".join(
                [f"{code.upper()}: {name}" for code, (_, name) in languages.items()])
            raise HTTPException(
                status_code=400,
                detail=f"Invalid language. Available options: {available_languages}"
            )
        language_id = languages[preferred_language_lower][0]
        update_fields.append("preferred_language_id = %s")
        update_values.append(language_id)

    if preferences.preferred_style is not None:
        preferred_style_lower = preferences.preferred_style.lower()

        if preferred_style_lower not in styles:
            available_styles = ", ".join(styles.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Invalid style. Available options: {available_styles}"
            )
        style_id = styles[preferred_style_lower]
        update_fields.append("preferred_style_id = %s")
        update_values.append(style_id)

    if not update_fields:
        raise HTTPException(
            status_code=400,
            detail=(
                f"No preferences provided for update. "
                f"Help: {bad_request_message_help}"
            )
        )

    update_values.append(current_user.username)
    update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE username = %s"

    cursor.execute(update_query, tuple(update_values))
    conn.commit()

    cursor.close()
    conn.close()

    updated_preferences = {}

    if preferences.preferred_language is not None:
        updated_preferences["preferred_language"] = preferences.preferred_language.upper(
        )

    if preferences.preferred_style is not None:
        updated_preferences["preferred_style"] = preferences.preferred_style

    return {
        "message": "Preferences updated successfully, check all preferences in get /users/me/preferences endpoint",
        "updated_preferences": updated_preferences
    }


@router.get("/users/me/preferences")
def get_preferences(current_user: UserInDB = Depends(verify_token)):
    return {
        "preferred_language": current_user.preferred_language,
        "preferred_style": current_user.preferred_style
    }
