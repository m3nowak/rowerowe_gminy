import fastapi

from rg_app.api_worker.dependencies.config import Config

router = fastapi.APIRouter(tags=["health"])


@router.get("/health")
async def health(config: Config):
    return {"status": "ok", "cfg": config.model_dump()}
