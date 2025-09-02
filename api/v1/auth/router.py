from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
)


router = APIRouter(prefix="/auth")


@router.post("/authorize")
async def authorize():
    ...


@router.post("/token")
async def token():
    ...
