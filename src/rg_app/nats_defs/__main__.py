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
@click.option("--dev", is_flag=True, default=True, help="Development mode")
def setup(url: str, creds: str | None, domain: str, inbox: str, mode: ty.Literal["local", "cloud"], dev: bool):
    asyncio.run(a_setup(url, creds, domain, inbox, mode, dev))


async def a_setup(url: str, creds: str | None, domain: str, inbox: str, mode: ty.Literal["local", "cloud"], dev: bool):
    nc = await nats.connect(url, user_credentials=creds, inbox_prefix=inbox)
    if domain:
        js = nc.jetstream(domain=domain)
    else:
        js = nc.jetstream()
    if mode == "local":
        await setup_local(js, dev=dev)
    elif mode == "cloud":
        if dev:
            raise ValueError("Cannot use dev mode with cloud")
        await setup_cloud(js)
    else:
        raise ValueError("Invalid mode")
    await nc.close()


def main():
    setup()


if __name__ == "__main__":
    setup()
