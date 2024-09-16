import typing as ty

import msgspec
import msgspec.json
import nats
import nats.aio
import nats.aio.client
import nats.aio.msg

from .common import CommonJsonable, SubjectLike, TextPayload
from .msg import ReplyMsg


async def connect(url: str | list[str], **kwargs):
    return await nats.connect(url, **kwargs)


def _standardize_subject(subject: SubjectLike | None) -> str:
    if subject is None:
        return ""
    elif isinstance(subject, list):
        return ".".join(subject)
    return ty.cast(str, subject)


def _standardize_payload(payload: TextPayload | None, json: CommonJsonable | None) -> bytes:
    if payload is not None:
        if isinstance(payload, str):
            return payload.encode()
        return payload
    elif json is not None:
        return msgspec.json.encode(json)
    else:
        return b""


class NatsClient(nats.aio.client.Client):
    # TODO: Implenent true tls support

    def __init__(self) -> None:
        super().__init__()

    async def publish(
        self,
        subject: SubjectLike,
        payload: TextPayload | None = None,
        reply: SubjectLike | None = None,
        headers: dict[str, str] | None = None,
        json: CommonJsonable | None = None,
    ):
        # subject: SubjectLike, raw_data: bytes | str | None = None, data_obj: ty.Any = None)
        final_subject = _standardize_subject(subject)
        final_reply = _standardize_subject(reply)
        final_payload = _standardize_payload(payload, json)
        await super().publish(final_subject, payload=final_payload, reply=final_reply, headers=headers)

    async def request(
        self,
        subject: SubjectLike,
        payload: TextPayload | None = None,
        timeout: float = 0.5,
        headers: dict[str, str] | None = None,
        json: CommonJsonable | None = None,
    ):
        final_subject = _standardize_subject(subject)
        final_payload = _standardize_payload(payload, json)
        response = await super().request(final_subject, payload=final_payload, timeout=timeout, headers=headers)
        return ReplyMsg(response)
