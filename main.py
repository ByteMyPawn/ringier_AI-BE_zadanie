from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routes.auth_routes import router as auth_router
from routes.authentication import router as login
from routes.weather_city import router as get_weather
from routes.user_management import router as users_router
from routes.user_settings import router as preferences_router
from routes.content_generation import router as generate_article_router
from routes.general import router as general_router

app = FastAPI()

# Include routers
app.include_router(auth_router)
app.include_router(login)
app.include_router(get_weather)
app.include_router(users_router)
app.include_router(preferences_router)
app.include_router(generate_article_router)
app.include_router(general_router)

# Handle CORS if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "message": "The requested resource was not found. Please check the URL or visit /help for more information."
        },
    )
