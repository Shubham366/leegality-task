from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
import logging

from connection_utils import db
from connection_utils.db.session import session, set_session_context
from connection_utils.redis.cache import Cache, CustomKeyMaker, RedisBackend
from v1.response import ApiResponse
from v1.router import router

logger = logging.getLogger(__name__)

def init_routers(app_: FastAPI) -> None:
    logger.info("Initializing routers")
    app_.include_router(router)
    logger.info("Routers initialized")

def init_cache() -> None:
    logger.info("Initializing cache")
    Cache.init(backend=RedisBackend(), key_maker=CustomKeyMaker())
    logger.info("Cache initialized")

def init_db() -> None:
    logger.info("Initializing database")
    db.init_db()
    logger.info("Database initialized")

def init_middleware(app_: FastAPI) -> None:
    @app_.middleware("http")
    async def db_session_middleware(request, call_next):
        set_session_context(id(request))
        try:
            return await call_next(request)
        finally:
            await session.remove()


def _bad_request_message(errors: list) -> str:
    messages = []
    locations = {".".join(str(part) for part in error.get("loc", ())) for error in errors}
    types = {error.get("type") for error in errors}
    if any(location.endswith("name") for location in locations):
        messages.append("Name missing")
    if any(name in location for location in locations for name in ("source", "destination")):
        messages.append("Source/destination missing")
    if any("latency" in location for location in locations) or "greater_than" in types:
        messages.append("latency must be greater than 0")
    return ", ".join(messages) or "bad request"


def init_exception_handlers(app_: FastAPI) -> None:
    @app_.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, exc: RequestValidationError):
        return ApiResponse.response_bad_request(message=_bad_request_message(exc.errors()))


def init_app() -> FastAPI:
    logger.info("Initializing app")
    app = FastAPI()
    init_middleware(app)
    init_exception_handlers(app)
    init_routers(app)
    init_cache()
    init_db()
    logger.info("App initialized")
    return app

app = init_app()