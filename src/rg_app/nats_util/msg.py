import typing as ty
from functools import cached_property

import msgspec.json
import nats
import nats.aio.client
import nats.aio.msg

from .common import CommonJsonable, TStructOrList


class ReplyMsg:
    def __init__(self, msg: nats.aio.msg.Msg):
        self._og_msg = msg

    @property
    def headers(self) -> dict[str, str]:
        return self._og_msg.headers or {}

    @property
    def subject(self) -> str:
        return self._og_msg.subject

    @property
    def data(self) -> bytes:
        return self._og_msg.data

    @cached_property
    def text(self) -> str:
        return self._og_msg.data.decode()

    @cached_property
    def json(self) -> CommonJsonable:
        return msgspec.json.decode(self.data)

    def json_as(self, t: ty.Type[TStructOrList]) -> TStructOrList:
        return msgspec.json.decode(self.data, type=t)
