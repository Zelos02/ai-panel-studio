from fastapi import APIRouter, Request

from ...schemas import HealthRead

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthRead)
def health(request: Request) -> HealthRead:
    settings = request.app.state.settings
    return HealthRead(
        status="ok",
        environment=settings.app_env,
        llm_provider=settings.llm_provider,
    )
