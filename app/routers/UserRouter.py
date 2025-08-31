from typing import Any

from fastapi import APIRouter

from app.services.UserService import get_user_service
import logging
import os


user_router = APIRouter(prefix="/user", tags=["user"])

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@user_router.get("/")
async def get_user() -> dict[str, Any]:
    logger.info("Getting user called")
    return get_user_service()
