from fastapi import APIRouter
from fastapi.responses import RedirectResponse
import dotenv
import os

dotenv.load_dotenv()
host_address = os.getenv("HOST_ADDRESS")

router = APIRouter()


@router.get("/", include_in_schema=False)
async def read_root():
    return RedirectResponse(url="/help")


@router.get("/help", tags=["General"])
async def help():
    return {
        "message": f"For help, visit documentation page: {host_address}:8000/docs "}
