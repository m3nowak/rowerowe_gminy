import asyncio
import logging
import random
import urllib.parse
from datetime import UTC, datetime, timedelta

import bs4
import httpx
import msgspec.json
import nats.js.errors
import polyline
import sqlalchemy as sa
from lxml import etree as ET
from lxml.builder import E
from nats import connect as nats_connect
from nats.aio.msg import Msg
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from rg_app.common.strava import StravaTokenManager
from rg_app.db.models import User

from .config import Config
from .models import ActivityPartial, ActivityStreamSet, LoginData
from .strava_auth import StravaAuth

logging.basicConfig(level=logging.INFO)


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


async def main(config: Config):
    nc = await nats_connect(
        config.nats.url, user_credentials=config.nats.creds_path, inbox_prefix=config.nats.inbox_prefix
    )
    js = nc.jetstream(domain=config.nats.js_domain)

    sa_engine = create_async_engine(
        config.db.get_url(),
    )
    sa_sm = async_sessionmaker(sa_engine, expire_on_commit=False)

    stm = StravaTokenManager(config.strava_client_id, config.get_strava_client_secret())

    kv = await js.key_value(config.nats.login_kv)

    async def handle_update(msg: Msg):
        msg_loaded: dict[str, str | int | dict] = msgspec.json.decode(msg.data)
        activity_id = msg_loaded.get("object_id")
        owner_id = msg_loaded.get("owner_id")
        assert isinstance(owner_id, int) and isinstance(activity_id, int)
        logging.info(f"Received update for activity {activity_id} for owner {owner_id}")
        try:
            owner_in_kv = await kv.get(str(owner_id))
        except nats.js.errors.KeyNotFoundError:
            owner_in_kv = None

        if owner_in_kv is None or owner_in_kv.value is None:
            logging.info(f"Owner {owner_id} not found in KV")
            await msg.respond(b"")
            return

        owner_login_data = msgspec.json.decode(owner_in_kv.value, type=LoginData)

        user_access_token = None

        async with sa_sm() as session:
            result = await session.execute(sa.select(User).filter(User.id == owner_id))
            user = result.scalars().one_or_none()
            if user is None:
                logging.info(f"Owner {owner_id} not found in DB")
                await msg.respond(b"")
                return

            # Check if the token is expired or missing
            now = datetime.now(UTC)
            if user.access_token is None or user.expires_at < now + timedelta(minutes=5):
                logging.info(f"Owner {owner_id} missing refresh token or token expired")
                async with stm.begin():
                    new_token = await stm.refresh(user.refresh_token)
                    user.access_token = new_token.access_token
                    user.expires_at = new_token.expires_at
                    await session.commit()
            user_access_token = user.access_token

        assert user_access_token is not None

        auth = StravaAuth(user_access_token)

        # Get activity detail
        da = None
        async with httpx.AsyncClient(auth=auth) as strava:
            resp = await strava.get(f"https://www.strava.com/api/v3/activities/{activity_id}")
            if resp.status_code == 200:
                da = msgspec.json.decode(resp.text, type=ActivityPartial)
            else:
                logging.info(f"Failed to get activity {activity_id}, status code {resp.status_code}")
                await msg.respond(b"")
                return

            # Check if activity is a Ride
            if da is None:
                logging.info(f"Activity {activity_id} not found")
                await msg.respond(b"")
                return
            if da.type != "Ride":
                logging.info(f"Activity {activity_id} is not a Ride")
                await msg.respond(b"")
                return
            if not da.map or not da.map.polyline:
                logging.info(f"Activity {activity_id} has no map or polyline")
                await msg.respond(b"")
                return

            streams = ["time", "latlng", "altitude", "distance"]
            resp = await strava.get(
                f"https://www.strava.com/api/v3/activities/{activity_id}/streams",
                params={"keys": ",".join(streams), "key_by_type": "true"},
            )
            if resp.status_code == 200:
                ass = msgspec.json.decode(resp.text, type=ActivityStreamSet)
            else:
                logging.info(f"Failed to get activity stream {activity_id}, status code {resp.status_code}")
                await msg.respond(b"")
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
            resp = await client.post(
                "https://wkolkokrece.pl/routes-traveled/import-route", files=files, data=data, headers=headers
            )
            resp.raise_for_status()
            logging.info(f"Activity {activity_id} added to wkk!")

        await msg.respond(b"")

    await nc.subscribe(config.nats.consumer_deliver_subject, cb=handle_update)

    logging.info(f"Subscribed to {config.nats.consumer_deliver_subject}")
    while True:
        await asyncio.sleep(1)
