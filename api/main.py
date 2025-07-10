from fastapi import FastAPI
import uvicorn

from config import api_settings


app = FastAPI(
    title=api_settings.title,
    description=api_settings.description,
    version=api_settings.version,
    openapi_url=api_settings.openapi_url,
    openapi_prefix=api_settings.openapi_prefix,
    docs_url=api_settings.docs_url,
    redoc_url=api_settings.redoc_url,
    root_path=api_settings.root_path,
)


"""
FOR DEVELOPMENT ONLY
"""
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
