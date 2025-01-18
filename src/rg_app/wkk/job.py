import asyncio
import logging
import random
import urllib.parse
from contextlib import AsyncExitStack
from datetime import datetime, timedelta

import bs4
import httpx
import msgspec.json
import nats.js.errors
import polyline
from lxml import etree as ET
from lxml.builder import E
from nats import connect as nats_connect
from nats.aio.msg import Msg
from nats.js.kv import KeyValue
from sqlalchemy.ext.asyncio import create_async_engine

from rg_app.common.internal.helpers import RIDE_LIKE_TYPES
from rg_app.common.msg import BaseStruct
from rg_app.common.strava import RateLimitManager, RLNatsConfig, StravaTokenManager
from rg_app.common.strava.activities import get_activity, get_activity_streams
from rg_app.common.strava.models.activity import ActivityStreamSet

from .config import Config

logging.basicConfig(level=logging.INFO)


class LoginData(BaseStruct):
    login: str
    password: str


def ass_to_gpx(ass: ActivityStreamSet, start_time: datetime) -> str:
    trak_points = []
    for latlng, altitude, time in zip(ass.latlng.data, ass.altitude.data, ass.time.data):
        dt = start_time + timedelta(seconds=time)
        trak_points.append(
            E.trkpt(
                E.ele(str(altitude)), E.time(dt.isoformat(timespec="seconds")), lat=str(latlng[0]), lon=str(latlng[1])
            )
        )
    gpx = E.gpx(
        E.trk(
            E.type("cycling"),
            E.trkseg(*trak_points),
        )
    )
    return ET.tostring(gpx).decode("utf-8")


def polyline_to_gpx(polyline_str: str) -> str:
    decoded_polyline = polyline.decode(polyline_str, geojson=True)
    gpx = E.gpx(
        E.trk(
            E.type("cycling"),
            E.trkseg(*[E.trkpt(lat=str(p[1]), lon=str(p[0])) for p in decoded_polyline]),
        )
    )
    return ET.tostring(gpx).decode("utf-8")


def extract_form_token(html: bytes) -> str:
    soup = bs4.BeautifulSoup(html, "html.parser")
    token = soup.select_one('head > meta[name="csrf-token"]')
    assert token is not None
    token_val = token["content"]
    assert isinstance(token_val, str)
    return token_val


def hadnle_update_factory(
    login_kv: KeyValue,
    stm: StravaTokenManager,
    rlm: RateLimitManager,
    common_http_client: httpx.AsyncClient,
    config: Config,
):
    async def handle_update(msg: Msg):
        msg_loaded: dict[str, str | int | dict] = msgspec.json.decode(msg.data)
        aspect_type = msg_loaded.get("aspect_type")
        activity_id = msg_loaded.get("object_id")
        owner_id = msg_loaded.get("owner_id")
        assert isinstance(owner_id, int) and isinstance(activity_id, int)
        logging.info(f"Received {aspect_type} for activity {activity_id} for owner {owner_id}")
        if aspect_type == "delete":
            logging.info(f"Activity {activity_id} deleted, skipping")
            await msg.ack()
            return
        try:
            owner_in_kv = await login_kv.get(str(owner_id))
        except nats.js.errors.KeyNotFoundError:
            owner_in_kv = None

        if owner_in_kv is None or owner_in_kv.value is None:
            logging.info(f"Owner {owner_id} not found in KV")
            await msg.ack()
            return

        owner_login_data = msgspec.json.decode(owner_in_kv.value, type=LoginData)

        strava_auth = None
        try:
            strava_auth = await stm.get_httpx_auth(owner_id)
        except ValueError:
            logging.info(f"Owner {owner_id} not found in DB")
            await msg.ack()
            return

        # Get activity detail
        try:
            da = await get_activity(common_http_client, activity_id, strava_auth, rlm)
        except httpx.HTTPStatusError as e:
            logging.info(f"Failed to get activity {activity_id}, status code {e.response.status_code}")
            await msg.ack()
            return

        # Check if activity is a Ride
        if da is None:
            logging.info(f"Activity {activity_id} not found")
            await msg.ack()
            return
        if da.sport_type not in RIDE_LIKE_TYPES:
            logging.info(f"Activity {activity_id} is not a Ride-Like activity")
            await msg.ack()
            return
        if not da.map or not da.map.polyline:
            logging.info(f"Activity {activity_id} has no map or polyline")
            await msg.ack()
            return

        try:
            ass = await get_activity_streams(common_http_client, activity_id, strava_auth, rlm)
        except httpx.HTTPStatusError as e:
            logging.info(f"Failed to get activity stream {activity_id}, status code {e.response.status_code}")
            await msg.ack()
            return

        # Decode polyline and save as GPX
        gpx_string = ass_to_gpx(ass, da.start_date)

        # generate strava url
        strava_url = f"https://www.strava.com/activities/{activity_id}"

        async with httpx.AsyncClient() as client:
            # get login page
            resp = await client.get("https://wkolkokrece.pl/login")
            token = extract_form_token(resp.read())
            await asyncio.sleep(random.random() * 2 + 1)
            login_data = {"email": owner_login_data.login, "password": owner_login_data.password, "_token": token}
            # post login data
            resp = await client.post("https://wkolkokrece.pl/login", data=login_data, follow_redirects=False)
            location = resp.headers.get("location")
            assert location is not None and location.endswith("/home")
            await asyncio.sleep(random.random() * 2 + 1)
            # navigate to add activity page
            resp = await client.get("https://wkolkokrece.pl/routes-traveled/import-route")
            await asyncio.sleep(random.random() * 4 + 3)

            # send data
            files = {"gpxFile": ("activity.gpx", gpx_string, "application/gpx+xml")}
            data = {"routeUrl": strava_url}
            headers = {
                "X-Requested-With": "XMLHttpRequest",
                "X-XSRF-TOKEN": urllib.parse.unquote(client.cookies["XSRF-TOKEN"]),
            }
            if config.dry_run:
                logging.info(f"Would have added activity {activity_id} to wkk")
            else:
                resp = await client.post(
                    "https://wkolkokrece.pl/routes-traveled/import-route", files=files, data=data, headers=headers
                )
                resp.raise_for_status()
                logging.info(f"Activity {activity_id} added to wkk!")

        await msg.ack()

    return handle_update


async def main(config: Config):
    async with AsyncExitStack() as ae_stack:
        nc = await nats_connect(
            config.nats.url,
            user_credentials=config.nats.creds_path,
            inbox_prefix=config.nats.inbox_prefix,
        )
        ae_stack.push_async_callback(nc.close)
        js = nc.jetstream(domain=config.nats.js_domain)
        logging.info(f"Connected to NATS at {config.nats.url}")
        login_kv = await js.key_value(config.nats.login_kv)
        logging.info(f"Connected to JetStream at {config.nats.js_domain}")

        sa_engine = create_async_engine(
            config.db.get_url(),
        )
        ae_stack.push_async_callback(sa_engine.dispose)

        rlm = RateLimitManager(RLNatsConfig(nc, config.nats.rate_limits_kv, config.nats.js_domain))
        rlm = await ae_stack.enter_async_context(rlm.begin())

        client_secret = config.strava.get_client_secret()
        assert client_secret is not None, "Strava client secret is not set"

        stm = StravaTokenManager(config.strava.client_id, client_secret, rlm, sa_engine)
        stm = await ae_stack.enter_async_context(stm.begin())

        common_http_client = await ae_stack.enter_async_context(httpx.AsyncClient())

        limits = await rlm.get_limits()

        if limits and limits.current_read_percent > config.rate_limit_teshold:
            logging.error(f"Rate limit reached {limits.current_read_percent} > {config.rate_limit_teshold}")
            return

        logging.info(f"Starting consumer {config.nats.consumer_name} for stream {config.nats.stream_name}")

        ps_inbox = (config.nats.inbox_prefix + ".").encode()
        sub = await js.pull_subscribe_bind(config.nats.consumer_name, config.nats.stream_name, inbox_prefix=ps_inbox)
        has_msgs = True
        handle_update = hadnle_update_factory(login_kv, stm, rlm, common_http_client, config)
        while has_msgs:
            try:
                msgs = await sub.fetch(1)
            except asyncio.TimeoutError:
                has_msgs = False
                break
            for msg in msgs:
                await handle_update(msg)

        logging.info(f"Emptied consumer {config.nats.consumer_name} for stream {config.nats.stream_name}")
