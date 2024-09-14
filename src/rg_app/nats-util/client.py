import typing as ty

import msgspec.json
import nats

SubjectLike = bytes | str | list[str]


async def connect(url, **kwargs):
    client = NatsClient(url, **kwargs)
    return await client.connect()


def _standardize_subject(subject: SubjectLike) -> str:
    if isinstance(subject, list):
        return ".".join(subject)
    elif isinstance(subject, bytes):
        return subject.decode()
    return ty.cast(str, subject)


class NatsClient:
    def __init__(self, url: str | list[str], **kwargs) -> None:
        self.url = url
        self.kwargs = kwargs
        self.nc = None

    async def connect(self):
        self.nc = await nats.connect(self.url, **self.kwargs)

    def _input_data_encode(self, raw_data: bytes | str | None, data_obj: ty.Any) -> bytes:
        final_data = None
        if raw_data is not None:
            if isinstance(raw_data, str):
                final_data = raw_data.encode()
            else:
                final_data = raw_data
        elif data_obj is not None:
            final_data = msgspec.json.encode(data_obj)
        else:
            raise ValueError("No data provided")
        return final_data

    async def publish(self, subject: SubjectLike, raw_data: bytes | str | None = None, data_obj: ty.Any = None):
        assert self.nc is not None, "NatsClient not connected"
        final_data = self._input_data_encode(raw_data, data_obj)
        await self.nc.publish(_standardize_subject(subject), final_data)

    async def close(self):
        if self.nc is not None:
            await self.nc.close()
