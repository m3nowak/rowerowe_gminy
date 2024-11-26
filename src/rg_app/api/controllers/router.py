from litestar import Router

from .region import RegionController
from .user import UserController

api_router = Router(path="/api", route_handlers=[UserController, RegionController])
