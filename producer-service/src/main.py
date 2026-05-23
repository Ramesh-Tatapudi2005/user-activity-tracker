from fastapi import FastAPI, status, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from src.schemas import UserActivityEvent
from src.publisher import publisher
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await publisher.connect()
        logger.info("Successfully connected to RabbitMQ.")
        yield
    finally:
        await publisher.close()
        logger.info("RabbitMQ connection closed.")

app = FastAPI(lifespan=lifespan)

# --- NEW: Override FastAPI's default 422 error with a 400 error ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "message": "Invalid UserActivityEvent payload", 
            "details": exc.errors()
        }
    )
# ------------------------------------------------------------------

@app.post("/api/v1/events/track", status_code=status.HTTP_202_ACCEPTED)
async def track_event(event: UserActivityEvent):
    try:
        await publisher.publish_event(event.model_dump())
        return {"message": "Event successfully accepted for processing"}
    except Exception as e:
        logger.error(f"Failed to publish event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during event publishing"
        )

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "healthy"}