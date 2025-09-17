from fastapi import (
    APIRouter,
    status,
)
from fastapi.responses import JSONResponse

from api.v1.ops.utils import (
    check_redis,
    check_celery_workers,
)
from tasks.main import app as celery_app
from config import settings


router = APIRouter(prefix="/ops")


@router.get("/status", status_code=status.HTTP_200_OK)
async def service_status() -> JSONResponse:
    return JSONResponse(
        content={
            "api": "ok",
            "redis": check_redis(settings.celery.broker_url),
            "celery": check_celery_workers(celery_app),
        }
    )
