from fastapi import APIRouter
from fastapi.responses import JSONResponse

from services.celery_worker.main import app as celery_app
from app.utils.health import (
    check_redis,
    check_celery_workers,
)
from app import status
from app.core import settings


router = APIRouter(prefix="/ops")


@router.get("/status", status_code=status.HTTP_200_OK)
async def service_status() -> JSONResponse:
    """
    Возвращает статус (состояние) внутренних сервисов.
    """

    return JSONResponse(
        content={
            "api": "ok",
            "redis": check_redis(settings.celery.broker_url),
            "celery": check_celery_workers(celery_app),
        }
    )
