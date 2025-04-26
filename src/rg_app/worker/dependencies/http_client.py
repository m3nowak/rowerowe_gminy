from contextlib import asynccontextmanager
from typing import Annotated

from faststream import ContextRepo, Depends
from httpx import AsyncClient

HTTP_CLIENT_REPO_KEY = "http_client"


@asynccontextmanager
async def lifespan(context: ContextRepo):
    async with AsyncClient() as http_client:
        context.set_global(HTTP_CLIENT_REPO_KEY, http_client)
        yield


def get_http_client(context: ContextRepo) -> AsyncClient:
    client: AsyncClient | None = context.get(HTTP_CLIENT_REPO_KEY)
    if client is None:
        raise ValueError("Key not found in context")
    return client


AsyncClientDI = Annotated[AsyncClient, Depends(get_http_client)]
