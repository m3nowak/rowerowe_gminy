"""
This is the only place where the global state of the application is stored.
To be removed when FastAPI and AsyncAPI can share common State object.
"""

from typing import Annotated

from fastapi import Depends

_STATE = {}


def _provide_state() -> dict:
    return _STATE


State = Annotated[dict, Depends(_provide_state)]
