from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.chat import router
from app.config.loader import load_config


def create_app(config_path: Path | None = None, *, coach_service=None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.coach_config = load_config(config_path)
        yield

    application = FastAPI(title="Routiq AI Coach", version="0.1.0", lifespan=lifespan)
    application.state.coach_service = coach_service
    application.include_router(router)

    @application.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, error: RequestValidationError):
        # Default errors echo untrusted inputs; never return them or log bodies.
        return JSONResponse(status_code=422, content={
            "code": "INVALID_REQUEST", "message": "Request does not match the chat schema."
        })

    @application.get("/health")
    def health():
        return {"status": "ok", "milestone": 1, "live_ai_enabled": application.state.coach_service is not None}

    @application.get("/ready")
    def ready():
        enabled = application.state.coach_service is not None
        return {"status": "live_demo_configured" if enabled else "foundation_ready", "chat_available": enabled,
                "authentication": "requires_verified_principal",
                "config_version": application.state.coach_config.document.version}

    return application


app = create_app()
