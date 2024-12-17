from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from httpx import AsyncClient as _AsyncClient

_HTTP_CLIENT_KEY = "http_client"


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with _AsyncClient() as client:
        setattr(app.state, _HTTP_CLIENT_KEY, client)
        yield


async def _provide_client(request: Request):
    return getattr(request.app.state, _HTTP_CLIENT_KEY)


AsyncClient = Annotated[_AsyncClient, Depends(_provide_client)]
