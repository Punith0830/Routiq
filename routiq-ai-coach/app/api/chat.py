"""Fail-closed boundary. No production authentication or AI routing in M1."""
from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.schemas.chat import ChatRequest, ChatResponse, ErrorResponse

router = APIRouter()


@dataclass(frozen=True)
class Principal:
    user_id: str


def authenticated_principal() -> Principal:
    # M5 must replace this with verified application authentication.
    # Client headers, body fields and arbitrary bearer tokens are never identity.
    raise HTTPException(status_code=401, detail="Verified authentication is not integrated")


@router.post("/api/v1/ai/chat", response_model=ChatResponse,
             responses={503: {"model": ErrorResponse}})
def chat(request: ChatRequest, http_request: Request,
         principal: Annotated[Principal, Depends(authenticated_principal)]):
    service = http_request.app.state.coach_service
    if service is not None:
        from app.services.chat_service import CoachUnavailable
        try:
            return service.respond(request, http_request.app.state.coach_config)
        except CoachUnavailable as error:
            return JSONResponse(status_code=503, content=ErrorResponse(
                code=error.code, message=str(error)
            ).model_dump())
    return JSONResponse(status_code=503, content=ErrorResponse(
        code="FOUNDATION_ONLY",
        message="AI routing and authorized habit services are not implemented yet.",
    ).model_dump())
