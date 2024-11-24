from litestar import Router

from .user import UserController

api_router = Router(path="/api", route_handlers=[UserController])
