import asyncio
import inspect
import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes import health_router, sessions_router, topics_router
from .config import Settings, get_settings
from .database import create_database, init_database
from .errors import AppError
from .events import EventHub
from .llm import build_llm_provider


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    engine, session_factory = create_database(resolved_settings.database_url)

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        init_database(engine)
        yield
        tasks = list(getattr(application.state, "discussion_tasks", {}).values())
        for task in tasks:
            if not task.done():
                task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        provider_close = getattr(application.state.llm_provider, "close", None)
        if provider_close is not None:
            close_result = provider_close()
            if inspect.isawaitable(close_result):
                await close_result
        engine.dispose()

    app = FastAPI(title="AI Panel Studio API", version="0.1.0", lifespan=lifespan)
    app.state.settings = resolved_settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.llm_provider = build_llm_provider(resolved_settings)
    app.state.event_hub = EventHub()
    app.state.discussion_tasks = {}
    app.state.discussion_states = {}

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[resolved_settings.frontend_origin],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "requestId": request.state.request_id,
                    "retryable": exc.retryable,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        safe_details = {"fields": [".".join(map(str, error["loc"])) for error in exc.errors()]}
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "提交的数据不符合要求，请检查后重试。",
                    "requestId": request.state.request_id,
                    "retryable": False,
                    "details": safe_details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logging.getLogger("panel_studio").exception(
            "Unhandled request error request_id=%s type=%s",
            request.state.request_id,
            type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "服务暂时遇到问题，请稍后重试。",
                    "requestId": request.state.request_id,
                    "retryable": True,
                    "details": {},
                }
            },
        )

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(topics_router, prefix="/api/v1")
    app.include_router(sessions_router, prefix="/api/v1")
    return app


app = create_app()
