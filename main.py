
from fastapi import FastAPI
from routes.auth_routes import router as auth_router
from routes.login import router as login
from routes.weather_city import router as get_weather
from routes.signup import router as signup_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(login)
app.include_router(get_weather)
app.include_router(signup_router)


def read_root():
    return {"message": "Welcome to the Weather API!"}
