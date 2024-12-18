from fastapi import APIRouter
from fastapi.responses import JSONResponse, RedirectResponse

router = APIRouter()


@router.get("/")
async def read_root():
    return RedirectResponse(url="/help")


@router.get("/help")
async def help():
    return {"message": "This is a placeholder for API documentation. Visit /login to access the login page."}
