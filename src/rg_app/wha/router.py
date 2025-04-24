from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from opentelemetry.trace import get_current_span

from rg_app.common.fastapi.dependencies.broker import NatsBroker
from rg_app.common.strava.models.webhook import WebhookUnion

from .config import ConfigDI

router = APIRouter()


@router.get("/health")
async def hc(broker: NatsBroker):
    """Health check for the webhook router."""
    if broker._connection is None or not broker._connection.is_connected:
        raise HTTPException(503, "NATS connection is not established")
    return {"status": "ok"}


@router.get("/webhook/{path_token}", tags=["webhook"])
async def webhook_validation(
    path_token: str,
    verify_token: Annotated[str, Query(alias="hub.verify_token", default="")],
    _: Annotated[str, Query(alias="hub.mode", default="")],
    challenge: Annotated[str, Query(alias="hub.challenge", default="")],
    config: ConfigDI,
) -> dict[str, str]:
    if verify_token != config.get_verify_token():
        raise HTTPException(401, "Invalid verify token")
    if path_token != config.get_verify_token():
        raise HTTPException(401, "Invalid path token")
    print("Webhook validation successful")
    return {"hub.challenge": challenge}


@router.post("/webhook/{path_token}", tags=["webhook"])
async def webhook_handler(
    path_token: str,
    data: WebhookUnion,
    broker: NatsBroker,
    config: ConfigDI,
    # tracer: Tracer,
    # otel_logger: Logger,
) -> dict[str, str]:
    if path_token != config.get_verify_token():
        raise HTTPException(401, "Invalid path token")
    span = get_current_span()
    span.set_attribute("user.id", data.root.owner_id)
    span.set_attribute("object.id", data.root.object_id)
    span.set_attribute("object.object_type", data.root.object_type)
    span.set_attribute("object.aspect_type", data.root.aspect_type)

    data_root = data.root
    subject = ".".join(
        [config.nats.subject_prefix, data_root.object_type, str(data_root.owner_id), str(data_root.object_id)]
    )

    await broker.publish(data_root, subject, stream=config.nats.stream)
    return {"status": "ok"}
