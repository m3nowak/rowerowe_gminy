import fastapi

from rg_app.api_worker.dependencies.config import Config

router = fastapi.APIRouter()


@router.get("/")
async def get_root(config: Config):
    return {"Hello": config.tlo}
