from utils.db_conn import get_db_connection
from fastapi import HTTPException


def get_user_preferred_language(username: str) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT l.code FROM users u JOIN languages l ON u.preferred_language_id = l.id WHERE u.username = %s", (username,))
    user_record = cursor.fetchone()
    cursor.close()
    conn.close()

    if user_record:
        return user_record[0]
    else:
        return "EN"  # Default to English if user not found


def validate_language_input(lang: str) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM languages")
    languages = cursor.fetchall()
    languages_dict = {row[1]: row[2] for row in languages}

    if lang not in languages_dict:
        cursor.close()
        conn.close()
        supported_languages = [
            f"  '{key}' for {value}  " for key,
            value in languages_dict.items()]
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Language '{lang}' is not supported.",
                "supported languages": supported_languages
            }
        )

    cursor.close()
    conn.close()
    return languages_dict
