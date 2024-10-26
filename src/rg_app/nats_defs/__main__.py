import asyncio
import typing as ty

import click
import nats

from .cloud import setup as setup_cloud
from .local import setup as setup_local


@click.command()
@click.argument("url", type=str)
@click.argument("mode", type=click.Choice(["local", "cloud"]))
@click.option("--creds", type=str, default=None, help="Credentials file")
@click.option("--domain", type=str, default="", help="JetStream domain")
@click.option("--inbox", type=str, default="_INBOX", help="Inbox prefix")
def setup(url: str, creds: str | None, domain: str, inbox: str, mode: ty.Literal["local", "cloud"]):
    asyncio.run(a_setup(url, creds, domain, inbox, mode))


async def a_setup(url: str, creds: str | None, domain: str, inbox: str, mode: ty.Literal["local", "cloud"]):
    nc = await nats.connect(url, user_credentials=creds, inbox_prefix=inbox)
    if domain:
        js = nc.jetstream(domain=domain)
    else:
        js = nc.jetstream()
    jsm = js._jsm
    if mode == "local":
        await setup_local(jsm)
    elif mode == "cloud":
        await setup_cloud(jsm)
    else:
        raise ValueError("Invalid mode")
    await nc.close()


if __name__ == "__main__":
    setup()
