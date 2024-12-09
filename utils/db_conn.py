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
    host = os.getenv("HOST_ADDRESS")

    # Database connection parameters
    conn = psycopg2.connect(
        dbname="weather_db",
        user=postgres_user,
        password=postgres_password,
        host=host,
        port="5432"
    )
    return conn
