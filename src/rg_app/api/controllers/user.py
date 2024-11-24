from litestar import Controller, get
from nats.aio.client import Client as NatsClient
from pydantic import TypeAdapter

from rg_app.common.internal.user_svc import UnlockedRequest

str_list_adapter = TypeAdapter(list[str])


class UserController(Controller):
    path = "/user"
    tags = ["user"]

    @get("/{user_id: int}/unlocked")
    async def get_user_unlocked(self, user_id: int, nats: NatsClient) -> list[str]:
        req = UnlockedRequest(user_id=user_id)
        resp = await nats.request("rg.svc.user.regions-unlocked", payload=req.model_dump_json().encode())
        return str_list_adapter.validate_json(resp.data)
