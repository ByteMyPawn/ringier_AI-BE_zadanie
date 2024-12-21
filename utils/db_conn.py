import os
import psycopg2
import dotenv

# Remove environment variables if they exist
os.environ.pop("POSTGRES_USER", None)
os.environ.pop("POSTGRES_PASSWORD", None)

# Load environment variables from .env file
dotenv.load_dotenv()


def get_db_connection():
    postgres_user = os.getenv("POSTGRES_USER")
    postgres_password = os.getenv("POSTGRES_PASSWORD")
    postgres_db = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST")

    # Database connection parameters
    conn = psycopg2.connect(
        dbname=postgres_db,
        user=postgres_user,
        password=postgres_password,
        host=host,
        port="5432"
    )

    conn.set_client_encoding('UTF8')

    return conn


# conn = get_db_connection()

# cursor = conn.cursor()

# cursor.execute(
#     "SELECT key_name, translation FROM translations WHERE language_code = 'SK';")
# translations = {str(key): str(value)
#                 for key, value in cursor.fetchall()}
# print(translations)

# cursor.close()
# conn.close()
