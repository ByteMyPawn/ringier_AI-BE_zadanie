from utils.db_conn import get_db_connection
from fastapi import HTTPException


def get_user_preferred_style(username: str) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT s.name FROM users u JOIN styles s ON u.preferred_style_id = s.id WHERE u.username = %s", (username,))
    user_record = cursor.fetchone()
    cursor.close()
    conn.close()

    if user_record:
        return user_record[0]
    else:
        return {}  # Return an empty dictionary if user not found


def validate_style_input(style: str) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM styles")
    styles = cursor.fetchall()

    styles_dict = {row[2]: row[1] for row in styles}

    if style not in styles_dict:
        cursor.close()
        conn.close()
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Style '{style}' is not supported.",
                "supported_styles": list(styles_dict.keys())
            }
        )

    cursor.close()
    conn.close()
    return styles_dict
