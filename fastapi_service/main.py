from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

from .database.session import init_db
from .api.routes import router as api_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    await init_db()
    yield
    print("Shutting down...")


app = FastAPI(
    title="ATM Popularity Prediction API",
    version="0.1.0",
    lifespan=lifespan
)
app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid request format"}
    )


@app.get("/")
async def root():
    return {"message": "ATM Popularity Prediction API", "status": "healthy"}