import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.approvals import router as approvals_router
from src.api.events import router as events_router
from src.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(json.dumps({"event": "startup", "message": f"Warden is running on port {settings.port}"}))
    yield


app = FastAPI(title="Warden Service", version="1.0.0", lifespan=lifespan)
app.include_router(events_router)
app.include_router(approvals_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(json.dumps({"event": "unhandled_exception", "path": request.url.path, "error": str(exc)}))
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@app.get("/health")
async def health_check():
    logger.info(json.dumps({"event": "health_check", "status": "success"}))
    return {"status": "ok"}


if __name__ == "__main__":
    from granian import Granian
    from granian.constants import Interfaces

    settings = get_settings()
    Granian(
        "src.main:app",
        address="0.0.0.0",
        port=settings.port,
        interface=Interfaces.ASGI,
        reload=True,
    ).serve()
