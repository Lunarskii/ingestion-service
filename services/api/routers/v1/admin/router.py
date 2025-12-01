from fastapi import APIRouter


router = APIRouter(prefix="/admin")


@router.post("/api-key")
async def create_api_key(): ...


@router.get("/api-key/{label}")
async def get_api_key(label: str): ...


@router.get("/api-keys")
async def get_api_keys(): ...


@router.patch("/api-key/{label}")
async def update_api_key(label: str): ...


@router.delete("/api-key/{label}")
async def delete_api_key(label: str): ...
