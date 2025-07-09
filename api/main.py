from fastapi import FastAPI
import uvicorn


app = FastAPI(
    title="Unknown",
    version="0.1.0",
)


"""
FOR DEVELOPMENT ONLY
"""
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
