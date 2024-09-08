from litestar import Litestar, get


@get("/authenticate")
def authenticate(code: str) -> dict[str, str]:
    #TODO
    return {"hello": "world"}


app = Litestar(route_handlers=[authenticate])