import asyncio

import nats

from .cloud import setup


async def main():
    nc = await nats.connect("nats://localhost:4222")
    js = nc.jetstream()
    jsm = js._jsm
    await setup(jsm)


if __name__ == "__main__":
    asyncio.run(main())
