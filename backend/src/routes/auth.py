from typing import Dict

from fastapi import APIRouter, Depends

from src.utils import api_token

auth_router = APIRouter(tags=["Auth"])


@auth_router.get("", dependencies=[Depends(api_token)])
async def api_key() -> Dict:
    return {"detail": "success"}
